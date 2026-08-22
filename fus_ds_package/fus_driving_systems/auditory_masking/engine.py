"""Deterministic mask generation, safe playback, and frozen WAV export."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import threading
import time

import numpy as np
from scipy.io import wavfile

from ._vendor.session_controller import SessionController
from .config import MaskingConfig


_RANDOM_LOCK = threading.RLock()


class MaskingPlaybackError(RuntimeError):
    """Raised when masking playback cannot be verified before sonication."""


@contextmanager
def _temporary_numpy_seed(seed):
    with _RANDOM_LOCK:
        previous_state = np.random.get_state()
        np.random.seed(seed)
        try:
            yield
        finally:
            np.random.set_state(previous_state)


@dataclass
class GeneratedMask:
    audio: np.ndarray
    sample_rate_hz: int
    config: MaskingConfig
    pulse_gate: np.ndarray | None = None
    matching_audio: np.ndarray | None = None
    background_audio: np.ndarray | None = None

    @property
    def duration_s(self):
        return len(self.audio) / float(self.sample_rate_hz)

    @property
    def peak(self):
        return float(np.max(np.abs(self.audio))) if len(self.audio) else 0.0

    @property
    def pcm16(self):
        return np.rint(np.clip(self.audio, -1.0, 1.0) * 32767).astype(np.int16)

    @property
    def audio_sha256(self):
        return hashlib.sha256(self.pcm16.tobytes()).hexdigest()

    def metadata(self):
        return {
            "format_version": 1,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Musarrat and Kop, Auditory Mask Generator, adapted for Radboud IGT",
            "source_doi": "10.5281/zenodo.20681923",
            "sample_rate_hz": self.sample_rate_hz,
            "channels": int(self.audio.shape[1]) if self.audio.ndim > 1 else 1,
            "samples": int(len(self.audio)),
            "duration_s": self.duration_s,
            "peak_digital_amplitude": self.peak,
            "audio_sha256": self.audio_sha256,
            "expected_pulses": self.config.expected_pulses,
            "pulse_repetition_interval_ms": self.config.pulse_repetition_interval_ms,
            "duty_cycle": self.config.duty_cycle,
            "config": self.config.to_dict(),
            "calibration_notice": (
                "Digital gain is not sound pressure level. Measure and approve the "
                "actual headphone SPL before participant exposure."
            ),
        }


def generate_mask(config):
    """Generate a deterministic stereo track shared by active and sham visits."""

    config = config.validate()
    parameters = config.to_hira_parameters()
    with _temporary_numpy_seed(config.random_seed):
        audio, _, gate, sample_rate, matching, background = SessionController().generate(
            parameters, config.playback_mode
        )

    expected_samples = round(config.total_duration_s * config.sample_rate_hz)
    audio = np.asarray(audio[:expected_samples], dtype=np.float32)
    if len(audio) < expected_samples:
        audio = np.pad(audio, ((0, expected_samples - len(audio)), (0, 0)))
    audio *= config.master_gain

    if not np.all(np.isfinite(audio)):
        raise ValueError("The generated masking track contains non-finite samples.")
    if np.max(np.abs(audio), initial=0.0) > 1.0:
        raise ValueError("The generated masking track exceeds digital full scale.")
    if np.max(np.abs(audio), initial=0.0) == 0.0:
        raise ValueError("The generated masking track is silent.")

    if gate is not None:
        gate = np.asarray(gate[:expected_samples], dtype=np.float32).copy()
        start_sample = round(config.pre_mask_s * config.sample_rate_hz)
        end_sample = round(
            (config.pre_mask_s + config.stimulation_duration_s) * config.sample_rate_hz
        )
        gate[:start_sample] = 0.0
        gate[end_sample:] = 0.0

    return GeneratedMask(
        audio=audio,
        sample_rate_hz=int(sample_rate),
        config=config,
        pulse_gate=gate,
        matching_audio=matching,
        background_audio=background,
    )


def save_mask(generated, wav_path):
    """Save a frozen stereo WAV and an adjacent auditable JSON sidecar."""

    target = Path(wav_path)
    if target.suffix.lower() != ".wav":
        target = target.with_suffix(".wav")
    target.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(str(target), generated.sample_rate_hz, generated.pcm16)
    metadata_path = target.with_suffix(".json")
    metadata_path.write_text(
        json.dumps(generated.metadata(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target, metadata_path


def load_mask(wav_path):
    """Load and verify an exported WAV against its original metadata sidecar."""

    target = Path(wav_path)
    metadata = json.loads(target.with_suffix(".json").read_text(encoding="utf-8"))
    sample_rate, pcm = wavfile.read(str(target))
    if pcm.dtype != np.int16:
        raise ValueError("Frozen masking WAV files must contain signed 16-bit PCM.")
    actual_hash = hashlib.sha256(np.ascontiguousarray(pcm).tobytes()).hexdigest()
    if actual_hash != metadata.get("audio_sha256"):
        raise ValueError("The masking WAV no longer matches its recorded SHA-256 hash.")
    if int(sample_rate) != int(metadata.get("sample_rate_hz", -1)):
        raise ValueError("The masking WAV sample rate does not match its metadata.")
    config = MaskingConfig(**metadata["config"]).validate()
    return GeneratedMask(
        audio=pcm.astype(np.float32) / 32767.0,
        sample_rate_hz=int(sample_rate),
        config=config,
    )


class SoundDevicePlayer:
    """Minimal, fail-closed audio adapter with explicit output-device checks."""

    def __init__(self, output_device=None, backend=None, clock=None):
        self.output_device = output_device
        self._backend = backend
        self._clock = clock or time.perf_counter

    @property
    def backend(self):
        if self._backend is None:
            try:
                self._backend = importlib.import_module("sounddevice")
            except ImportError as error:
                raise MaskingPlaybackError(
                    "Audio masking requires sounddevice. Install it in the active "
                    "FUS_DS_PACKAGE environment with: python -m pip install sounddevice"
                ) from error
        return self._backend

    def check_output(self, sample_rate_hz):
        try:
            device = self.backend.query_devices(self.output_device, "output")
            if int(device.get("max_output_channels", 0)) < 2:
                raise MaskingPlaybackError("The selected output device does not provide stereo audio.")
            self.backend.check_output_settings(
                device=self.output_device,
                channels=2,
                samplerate=sample_rate_hz,
                dtype="float32",
            )
            return dict(device)
        except MaskingPlaybackError:
            raise
        except Exception as error:
            raise MaskingPlaybackError(
                "The selected headphones or output device cannot play the masking track."
            ) from error

    def play(self, generated):
        requested_at = self._clock()
        try:
            self.backend.play(
                np.asarray(generated.audio, dtype=np.float32),
                samplerate=generated.sample_rate_hz,
                device=self.output_device,
                blocking=False,
            )
            stream = self.backend.get_stream()
            stream_started_at = self._clock()
            if not getattr(stream, "active", False):
                raise MaskingPlaybackError("The headphone playback stream did not start.")
            latency = getattr(stream, "latency", 0.0)
            if hasattr(latency, "output"):
                latency = latency.output
            latency_s = max(0.0, float(latency or 0.0))
            return {
                "requested_at": requested_at,
                "stream_started_at": stream_started_at,
                "latency_s": latency_s,
                "estimated_output_start_at": stream_started_at + latency_s,
            }
        except MaskingPlaybackError:
            raise
        except Exception as error:
            raise MaskingPlaybackError("Headphone playback failed before sonication.") from error

    def wait(self):
        try:
            self.backend.wait()
        except Exception as error:
            raise MaskingPlaybackError("Masking playback stopped unexpectedly.") from error

    def stop(self):
        if self._backend is not None:
            self._backend.stop()
