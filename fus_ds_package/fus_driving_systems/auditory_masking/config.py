"""Validated, serializable settings for research-only auditory masking."""

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


BACKGROUND_TYPES = (
    "White Noise",
    "Colored Noise",
    "Narrowband Noise",
    "Hybrid Ultrasound Mask",
    "Auditory Mondrian",
)

PLAYBACK_MODES = ("Matching Only", "Background Only", "Combined")


@dataclass(frozen=True)
class MaskingConfig:
    """Mask settings independent of any particular ultrasound manufacturer.

    ``ultrasound_frequency_khz`` is recorded for provenance only. It is never
    sent to headphones. The audible carrier is ``audio_carrier_hz``.
    """

    enabled: bool = True
    stimulation_duration_s: float = 90.0
    pulse_repetition_frequency_hz: float = 5.0
    pulse_duration_ms: float = 20.0
    ultrasound_frequency_khz: float = 300.0
    audio_carrier_hz: float = 14000.0
    sample_rate_hz: int = 44100
    pre_mask_s: float = 1.0
    post_mask_s: float = 1.0
    playback_mode: str = "Combined"
    background_type: str = "White Noise"
    background_color: str = "Pink"
    background_center_hz: float = 1000.0
    background_bandwidth_hz: float = 200.0
    matching_gain: float = 0.50
    background_gain: float = 0.50
    master_gain: float = 1.00
    stereo_pan: float = 0.0
    pulse_ramp_ms: float = 5.0
    background_ramp_s: float = 0.20
    signal_to_noise_ratio_db: float | None = None
    random_seed: int = 15287005
    audio_device: str | int | None = None
    headphones_calibrated: bool = False

    @property
    def pulse_repetition_interval_ms(self) -> float:
        return 1000.0 / self.pulse_repetition_frequency_hz

    @property
    def duty_cycle(self) -> float:
        return self.pulse_duration_ms / self.pulse_repetition_interval_ms

    @property
    def total_duration_s(self) -> float:
        return self.pre_mask_s + self.stimulation_duration_s + self.post_mask_s

    @property
    def expected_pulses(self) -> int:
        return int(round(self.stimulation_duration_s * self.pulse_repetition_frequency_hz))

    def validate(self) -> "MaskingConfig":
        for label, value in (
            ("Stimulation duration", self.stimulation_duration_s),
            ("Pulse repetition frequency", self.pulse_repetition_frequency_hz),
            ("Pulse duration", self.pulse_duration_ms),
            ("Ultrasound frequency", self.ultrasound_frequency_khz),
            ("Audio carrier frequency", self.audio_carrier_hz),
        ):
            if not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{label} must be a finite positive number.")

        if self.sample_rate_hz < 8000:
            raise ValueError("The audio sample rate must be at least 8,000 Hz.")
        if self.audio_carrier_hz >= self.sample_rate_hz / 2:
            raise ValueError("The audible carrier must remain below the Nyquist frequency.")
        if self.pulse_duration_ms > self.pulse_repetition_interval_ms:
            raise ValueError("Pulse duration cannot exceed the pulse repetition interval.")
        if self.pulse_ramp_ms < 0 or self.pulse_ramp_ms > self.pulse_duration_ms / 2:
            raise ValueError("The pulse ramp must be between zero and half the pulse duration.")
        if self.pre_mask_s < 0 or self.post_mask_s < 0:
            raise ValueError("Pre-mask and post-mask intervals cannot be negative.")
        if self.background_ramp_s < 0:
            raise ValueError("The background ramp cannot be negative.")
        if self.playback_mode not in PLAYBACK_MODES:
            raise ValueError(f"Playback mode must be one of {PLAYBACK_MODES}.")
        if self.background_type not in BACKGROUND_TYPES:
            raise ValueError(f"Background type must be one of {BACKGROUND_TYPES}.")
        if self.background_color not in ("White", "Pink", "Brown", "Blue", "Violet"):
            raise ValueError("Unsupported colored-noise selection.")
        for label, value in (
            ("Matching gain", self.matching_gain),
            ("Background gain", self.background_gain),
            ("Master gain", self.master_gain),
        ):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{label} must be between 0 and 1.")
        if not -1 <= self.stereo_pan <= 1:
            raise ValueError("Stereo pan must be between -1 (left) and 1 (right).")
        if self.signal_to_noise_ratio_db is not None and not math.isfinite(
            self.signal_to_noise_ratio_db
        ):
            raise ValueError("Signal-to-noise ratio must be finite when provided.")
        if not 0 <= int(self.random_seed) <= 2**32 - 1:
            raise ValueError("Random seed must fit within an unsigned 32-bit integer.")
        return self

    def to_hira_parameters(self) -> dict:
        """Map the IGT timing definition onto the original mask-generator API."""

        self.validate()
        pulse_start_ms = self.pre_mask_s * 1000.0
        pulse_end_ms = (self.pre_mask_s + self.stimulation_duration_s) * 1000.0
        snr = (
            None
            if self.signal_to_noise_ratio_db is None
            else 10 ** (self.signal_to_noise_ratio_db / 20.0)
        )
        return {
            "fs": self.sample_rate_hz,
            "duration": self.total_duration_s,
            "carrier_freq": self.audio_carrier_hz,
            "enable_carrier": True,
            "prf": self.pulse_repetition_frequency_hz,
            "pulse_width": self.pulse_duration_ms / 1000.0,
            "snr": snr,
            "ramp_len": self.pulse_ramp_ms / 1000.0,
            "ramp_shape": "Tukey" if self.pulse_ramp_ms > 0 else "None",
            "num_trains": 1,
            "offset": self.pre_mask_s,
            "pulse_start_ms": pulse_start_ms,
            "pulse_end_ms": pulse_end_ms,
            "pulse_volume": self.matching_gain,
            "bg_type": self.background_type,
            "bg_volume": self.background_gain,
            "bg_start_ms": 0,
            "bg_end_ms": self.total_duration_s * 1000.0,
            "bg_ramp_shape": "Tukey" if self.background_ramp_s > 0 else "None",
            "bg_ramp_length": self.background_ramp_s,
            "bg_noise_color": self.background_color,
            "bg_center_freq": self.background_center_hz,
            "bg_bandwidth": self.background_bandwidth_hz,
            "pan": self.stereo_pan,
            "hybrid_mask_settings": {
                "prf_harmonics": 10,
                "harmonic_bandwidth": 200,
                "mondrian_density": 4,
                "mondrian_tone_duration_ms": 500,
                "prf_mask_weight": 0.5,
                "mondrian_weight": 0.3,
                "broadband_weight": 0.2,
            },
            "mondrian_mask_settings": {
                "density": 8,
                "tone_duration_ms": 500,
                "pf_min": 20,
                "pf_max": min(15000, self.sample_rate_hz / 2 - 100),
                "prf_min": 1000,
                "prf_max": min(15000, self.sample_rate_hz / 2 - 100),
                "duty_cycle": 50,
            },
        }

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return target

    @classmethod
    def from_json(cls, path):
        values = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**values).validate()

    @classmethod
    def from_sequence(cls, sequence, **overrides) -> "MaskingConfig":
        """Populate the mask directly from an existing Radboud IGT sequence."""

        repetition_interval = float(sequence.pulse_rep_int)
        if repetition_interval <= 0:
            raise ValueError("The IGT pulse repetition interval must be positive.")
        values = {
            "pulse_repetition_frequency_hz": 1000.0 / repetition_interval,
            "pulse_duration_ms": float(sequence.pulse_dur),
            "ultrasound_frequency_khz": float(sequence.oper_freq),
        }
        if getattr(sequence, "pulse_train_rep_dur", None) is not None:
            values["stimulation_duration_s"] = float(sequence.pulse_train_rep_dur)
        values.update(overrides)
        return cls(**values).validate()
