"""One-start auditory masking orchestration around buffered IGT sequences."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from .citation import SOFTWARE_CITATION, SOFTWARE_DOI
from .config import MaskingConfig
from .engine import SoundDevicePlayer, generate_mask


@dataclass
class SessionResult:
    condition: str
    audio_sha256: str
    expected_pulses: int
    events: list = field(default_factory=list)
    audio_latency_s: float = 0.0
    scheduled_pre_mask_s: float = 0.0
    actual_pre_mask_s: float = 0.0

    def to_dict(self, reveal_condition=False):
        output = {
            "software_doi": SOFTWARE_DOI,
            "software_citation": SOFTWARE_CITATION,
            "condition": self.condition if reveal_condition else "masked",
            "audio_sha256": self.audio_sha256,
            "expected_pulses": self.expected_pulses,
            "audio_latency_s": self.audio_latency_s,
            "scheduled_pre_mask_s": self.scheduled_pre_mask_s,
            "actual_pre_mask_s": self.actual_pre_mask_s,
            "events": self.events,
        }
        return output


class MaskedIGTSession:
    """Execute an IGT session or non-sonicating sham under the same mask.

    The caller remains responsible for connecting, validating, and buffering
    the active IGT sequence. A sham never calls ``execute_sequence``.
    """

    def __init__(
        self,
        config,
        player=None,
        log_path=None,
        logger=None,
        clock=None,
        sleeper=None,
    ):
        self.config = config.validate()
        self.player = player or SoundDevicePlayer(output_device=config.audio_device)
        self.log_path = Path(log_path) if log_path else None
        self.logger = logger
        self.clock = clock or time.perf_counter
        self.sleeper = sleeper or time.sleep

    def _record(self, result, event, **details):
        row = {
            "event": event,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "monotonic_s": self.clock(),
            **details,
        }
        result.events.append(row)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(row, sort_keys=True) + "\n")
        if self.logger is not None:
            self.logger.info("Auditory masking event: %s", event)
        return row

    def run(self, driving_system, sequence, sequence_two=None, condition="active", mask=None):
        if condition not in ("active", "sham"):
            raise ValueError("Condition must be either 'active' or 'sham'.")
        if condition == "active" and driving_system is None:
            raise ValueError("An active session requires an initialized IGT driving system.")
        if sequence is not None and getattr(sequence, "wait_for_trigger", False):
            raise ValueError(
                "External-triggered IGT sequences need a shared hardware trigger. "
                "The software-timed masking workflow requires wait_for_trigger=False."
            )
        if self.config.enabled and not self.config.headphones_calibrated:
            raise ValueError(
                "Headphone masking has not been marked as calibrated and approved. "
                "Run the audio test, measure the delivered SPL, obtain the required "
                "institutional approval, then set headphones_calibrated=true."
            )

        if not self.config.enabled:
            result = SessionResult(condition, "disabled", self.config.expected_pulses)
            self._record(result, "masking_disabled")
            if condition == "active":
                driving_system.execute_sequence(sequence, sequence_two)
            else:
                self.sleeper(self.config.stimulation_duration_s)
            self._record(result, "session_complete")
            return result

        generated = mask or generate_mask(self.config)
        if generated.config != self.config:
            raise ValueError("The frozen masking track does not match this session configuration.")
        result = SessionResult(
            condition=condition,
            audio_sha256=generated.audio_sha256,
            expected_pulses=self.config.expected_pulses,
            scheduled_pre_mask_s=self.config.pre_mask_s,
        )
        self.player.check_output(generated.sample_rate_hz)
        self._record(
            result,
            "audio_output_verified",
            sample_rate_hz=generated.sample_rate_hz,
            audio_sha256=generated.audio_sha256,
        )

        started = False
        try:
            timing = self.player.play(generated)
            started = True
            output_start = timing["estimated_output_start_at"]
            result.audio_latency_s = timing["latency_s"]
            self._record(result, "mask_started", estimated_audio_latency_s=result.audio_latency_s)

            planned_onset = output_start + self.config.pre_mask_s
            delay = planned_onset - self.clock()
            if delay > 0:
                self.sleeper(delay)

            dispatch_at = self.clock()
            result.actual_pre_mask_s = dispatch_at - output_start
            self._record(
                result,
                "stimulation_window_started",
                pre_mask_s=result.actual_pre_mask_s,
            )

            if condition == "active":
                driving_system.execute_sequence(sequence, sequence_two)
            else:
                self.sleeper(self.config.stimulation_duration_s)

            self._record(result, "stimulation_window_complete")
            self.player.wait()
            self._record(result, "mask_complete")
            self._record(result, "session_complete")
            return result
        except BaseException as error:
            self._record(result, "session_aborted", error_type=type(error).__name__)
            if started:
                self.player.stop()
            raise
