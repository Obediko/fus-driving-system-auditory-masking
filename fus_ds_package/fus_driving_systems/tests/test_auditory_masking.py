"""Hardware-free regression coverage for the research-only IGT masking adapter."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from fus_driving_systems.auditory_masking import (
    MaskedIGTSession,
    MaskingConfig,
    MaskingPlaybackError,
    SOFTWARE_AUTHORS,
    SOFTWARE_CITATION,
    SOFTWARE_DOI,
    SoundDevicePlayer,
    UPSTREAM_MASKING_DOI,
    generate_mask,
    load_mask,
    save_mask,
)


class SimulatedClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def sleep(self, seconds):
        if seconds < 0:
            raise AssertionError("Negative sleep requested.")
        self.value += seconds


class SimulatedPlayer:
    def __init__(self, clock, fail=False):
        self.clock = clock
        self.fail = fail
        self.events = []
        self.last_audio_sha256 = None

    def check_output(self, sample_rate_hz):
        self.events.append(("check", sample_rate_hz))
        if self.fail:
            raise MaskingPlaybackError("Headphones unavailable.")
        return {"max_output_channels": 2}

    def play(self, generated):
        self.events.append(("play", self.clock()))
        self.last_audio_sha256 = generated.audio_sha256
        return {
            "requested_at": self.clock(),
            "stream_started_at": self.clock(),
            "latency_s": 0.05,
            "estimated_output_start_at": self.clock() + 0.05,
        }

    def wait(self):
        self.events.append(("wait", self.clock()))

    def stop(self):
        self.events.append(("stop", self.clock()))


class SimulatedSequence:
    wait_for_trigger = False
    pulse_rep_int = 200.0
    pulse_dur = 20.0
    pulse_train_rep_dur = 1.0
    oper_freq = 300.0


class SimulatedIGT:
    def __init__(self, clock, fail=False):
        self.clock = clock
        self.fail = fail
        self.calls = []

    def execute_sequence(self, first, second):
        self.calls.append((first, second, self.clock()))
        if self.fail:
            raise RuntimeError("Simulated generator fault.")
        self.clock.sleep(1.0)


class AuditoryMaskingTests(unittest.TestCase):
    def setUp(self):
        self.config = MaskingConfig(
            stimulation_duration_s=1.0,
            pulse_repetition_frequency_hz=5.0,
            pulse_duration_ms=20.0,
            audio_carrier_hz=1000.0,
            sample_rate_hz=8000,
            pre_mask_s=0.2,
            post_mask_s=0.2,
            pulse_ramp_ms=2.0,
            background_ramp_s=0.05,
            headphones_calibrated=True,
        )

    def test_protocol_timing_and_pulse_count(self):
        mask = generate_mask(self.config)
        self.assertEqual(mask.audio.shape, (11200, 2))
        self.assertEqual(mask.config.expected_pulses, 5)
        self.assertAlmostEqual(mask.config.pulse_repetition_interval_ms, 200.0)
        self.assertAlmostEqual(mask.config.duty_cycle, 0.10)
        onsets = np.flatnonzero(
            (mask.pulse_gate[1:] > 0.0) & (mask.pulse_gate[:-1] <= 0.0)
        )
        self.assertEqual(len(onsets), 5)
        self.assertTrue(np.allclose(np.diff(onsets) / self.config.sample_rate_hz, 0.2))

    def test_same_seed_produces_identical_active_and_sham_audio(self):
        first = generate_mask(self.config)
        second = generate_mask(self.config)
        np.testing.assert_array_equal(first.audio, second.audio)
        self.assertEqual(first.audio_sha256, second.audio_sha256)

    def test_different_seed_changes_background(self):
        first = generate_mask(self.config)
        second = generate_mask(replace(self.config, random_seed=self.config.random_seed + 1))
        self.assertNotEqual(first.audio_sha256, second.audio_sha256)

    def test_generation_restores_global_random_state(self):
        np.random.seed(12345)
        expected = np.random.random(4)
        np.random.seed(12345)
        generate_mask(self.config)
        np.testing.assert_array_equal(np.random.random(4), expected)

    def test_waveform_is_finite_stereo_and_bounded(self):
        mask = generate_mask(self.config)
        self.assertEqual(mask.audio.dtype, np.float32)
        self.assertEqual(mask.audio.shape[1], 2)
        self.assertTrue(np.isfinite(mask.audio).all())
        self.assertGreater(mask.peak, 0)
        self.assertLessEqual(mask.peak, 1)

    def test_background_modes_generate_without_colorednoise_dependency(self):
        for background_type in (
            "White Noise",
            "Colored Noise",
            "Narrowband Noise",
            "Auditory Mondrian",
        ):
            with self.subTest(background_type=background_type):
                mask = generate_mask(replace(self.config, background_type=background_type))
                self.assertGreater(mask.peak, 0)

    def test_save_and_load_frozen_mask(self):
        original = generate_mask(self.config)
        with tempfile.TemporaryDirectory() as directory:
            wav_path, json_path = save_mask(original, Path(directory) / "mask.wav")
            metadata = json.loads(json_path.read_text(encoding="utf-8"))
            restored = load_mask(wav_path)
            self.assertEqual(metadata["expected_pulses"], 5)
            self.assertEqual(metadata["audio_sha256"], original.audio_sha256)
            self.assertEqual(restored.audio_sha256, original.audio_sha256)

    def test_published_software_citation_is_exposed(self):
        self.assertEqual(SOFTWARE_AUTHORS, ("Apochi Obed", "Nikolai Axmacher"))
        self.assertEqual(SOFTWARE_DOI, "10.5281/zenodo.22059704")
        self.assertIn("Apochi, O., & Axmacher, N.", SOFTWARE_CITATION)
        self.assertIn(f"https://doi.org/{SOFTWARE_DOI}", SOFTWARE_CITATION)

    def test_exported_metadata_preserves_adaptation_and_upstream_dois(self):
        metadata = generate_mask(self.config).metadata()
        self.assertEqual(metadata["software_doi"], SOFTWARE_DOI)
        self.assertEqual(metadata["software_authors"], list(SOFTWARE_AUTHORS))
        self.assertEqual(metadata["software_citation"], SOFTWARE_CITATION)
        self.assertEqual(metadata["source_doi"], UPSTREAM_MASKING_DOI)

    def test_tampered_wav_is_rejected(self):
        original = generate_mask(self.config)
        with tempfile.TemporaryDirectory() as directory:
            wav_path, _ = save_mask(original, Path(directory) / "mask.wav")
            raw = bytearray(wav_path.read_bytes())
            raw[-4] ^= 1
            wav_path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_mask(wav_path)

    def test_active_executes_once_after_mask_onset(self):
        clock = SimulatedClock()
        player = SimulatedPlayer(clock)
        driver = SimulatedIGT(clock)
        sequence = SimulatedSequence()
        runner = MaskedIGTSession(
            self.config,
            player=player,
            clock=clock,
            sleeper=clock.sleep,
        )
        result = runner.run(driver, sequence, condition="active")
        self.assertEqual(len(driver.calls), 1)
        self.assertAlmostEqual(result.actual_pre_mask_s, self.config.pre_mask_s)
        self.assertEqual(result.expected_pulses, 5)
        self.assertEqual(result.to_dict()["condition"], "masked")
        self.assertEqual(result.to_dict(reveal_condition=True)["condition"], "active")
        self.assertEqual(player.events[0][0], "check")
        self.assertEqual(player.events[1][0], "play")

    def test_sham_never_energizes_generator_and_uses_same_audio(self):
        active_clock = SimulatedClock()
        active_player = SimulatedPlayer(active_clock)
        active_driver = SimulatedIGT(active_clock)
        sequence = SimulatedSequence()
        active = MaskedIGTSession(
            self.config,
            player=active_player,
            clock=active_clock,
            sleeper=active_clock.sleep,
        ).run(active_driver, sequence, condition="active")

        sham_clock = SimulatedClock()
        sham_player = SimulatedPlayer(sham_clock)
        sham = MaskedIGTSession(
            self.config,
            player=sham_player,
            clock=sham_clock,
            sleeper=sham_clock.sleep,
        ).run(None, sequence, condition="sham")
        self.assertEqual(active.audio_sha256, sham.audio_sha256)
        self.assertEqual(active_player.last_audio_sha256, sham_player.last_audio_sha256)
        self.assertAlmostEqual(active_clock(), sham_clock())

    def test_missing_headphones_prevents_generator_execution(self):
        clock = SimulatedClock()
        driver = SimulatedIGT(clock)
        runner = MaskedIGTSession(
            self.config,
            player=SimulatedPlayer(clock, fail=True),
            clock=clock,
            sleeper=clock.sleep,
        )
        with self.assertRaises(MaskingPlaybackError):
            runner.run(driver, SimulatedSequence(), condition="active")
        self.assertEqual(driver.calls, [])

    def test_uncalibrated_headphones_fail_closed(self):
        clock = SimulatedClock()
        driver = SimulatedIGT(clock)
        config = replace(self.config, headphones_calibrated=False)
        runner = MaskedIGTSession(config, player=SimulatedPlayer(clock))
        with self.assertRaisesRegex(ValueError, "calibrated"):
            runner.run(driver, SimulatedSequence(), condition="active")
        self.assertEqual(driver.calls, [])

    def test_generator_failure_stops_mask(self):
        clock = SimulatedClock()
        player = SimulatedPlayer(clock)
        runner = MaskedIGTSession(
            self.config,
            player=player,
            clock=clock,
            sleeper=clock.sleep,
        )
        with self.assertRaisesRegex(RuntimeError, "generator fault"):
            runner.run(SimulatedIGT(clock, fail=True), SimulatedSequence())
        self.assertEqual(player.events[-1][0], "stop")

    def test_external_trigger_is_rejected(self):
        sequence = SimulatedSequence()
        sequence.wait_for_trigger = True
        with self.assertRaisesRegex(ValueError, "shared hardware trigger"):
            MaskedIGTSession(self.config).run(None, sequence, condition="sham")

    def test_sequence_settings_are_imported(self):
        config = MaskingConfig.from_sequence(
            SimulatedSequence(),
            audio_carrier_hz=1000,
            sample_rate_hz=8000,
        )
        self.assertEqual(config.pulse_repetition_frequency_hz, 5)
        self.assertEqual(config.pulse_duration_ms, 20)
        self.assertEqual(config.stimulation_duration_s, 1)

    def test_invalid_pulse_width_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "repetition interval"):
            replace(self.config, pulse_duration_ms=201).validate()

    def test_invalid_audio_carrier_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Nyquist"):
            replace(self.config, audio_carrier_hz=4000).validate()

    def test_output_backend_must_start_active_stream(self):
        class InactiveBackend:
            def play(self, *_args, **_kwargs):
                return None

            def get_stream(self):
                return type("InactiveStream", (), {"active": False, "latency": 0})()

        player = SoundDevicePlayer(backend=InactiveBackend())
        with self.assertRaisesRegex(MaskingPlaybackError, "did not start"):
            player.play(generate_mask(self.config))

    def test_dortmund_preset_matches_exact_pmErc_protocol(self):
        root = Path(__file__).resolve().parents[3]
        preset = MaskingConfig.from_json(
            root / "standalone_driving_system_software" / "masking_config_pmErC.json"
        )
        self.assertEqual(preset.ultrasound_frequency_khz, 300)
        self.assertEqual(preset.pulse_repetition_frequency_hz, 5)
        self.assertEqual(preset.pulse_duration_ms, 20)
        self.assertEqual(preset.stimulation_duration_s, 90)
        self.assertEqual(preset.expected_pulses, 450)
        self.assertFalse(preset.headphones_calibrated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
