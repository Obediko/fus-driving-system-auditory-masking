"""Configure, test, export, and run the Dortmund IGT auditory-masking workflow."""

from dataclasses import replace
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from fus_driving_systems.auditory_masking import (
    MaskingConfig,
    SoundDevicePlayer,
    generate_mask,
    save_mask,
)
from fus_driving_systems.auditory_masking.config import BACKGROUND_TYPES, PLAYBACK_MODES


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIRECTORY / "masking_config_pmErC.json"
RUNNER_PATH = SCRIPT_DIRECTORY / "standalone_igt_pmErC.py"


class AuditoryMaskingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dortmund IGT D054 | TUS Auditory Masking")
        self.root.minsize(860, 700)
        self.config = MaskingConfig.from_json(CONFIG_PATH)
        self.generated = None
        self.player = None
        self.running_process = None
        self.messages = queue.Queue()
        self.variables = {}
        self._build_interface()
        self._load_values()
        self.root.after(150, self._consume_messages)

    def _field(self, frame, row, column, label, name, width=16):
        ttk.Label(frame, text=label).grid(
            row=row, column=column * 2, sticky="w", padx=(10, 4), pady=5
        )
        variable = tk.StringVar()
        self.variables[name] = variable
        ttk.Entry(frame, textvariable=variable, width=width).grid(
            row=row, column=column * 2 + 1, sticky="ew", padx=(0, 12), pady=5
        )

    def _combo(self, frame, row, column, label, name, choices, width=18):
        ttk.Label(frame, text=label).grid(
            row=row, column=column * 2, sticky="w", padx=(10, 4), pady=5
        )
        variable = tk.StringVar()
        self.variables[name] = variable
        ttk.Combobox(
            frame,
            textvariable=variable,
            values=choices,
            state="readonly",
            width=width,
        ).grid(row=row, column=column * 2 + 1, sticky="ew", padx=(0, 12), pady=5)

    def _build_interface(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text="IGT D054 / Imasonic 15287-1005 auditory masking",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Research use only. Identical frozen audio is required for active and sham visits.",
            foreground="#5c5c5c",
        ).pack(anchor="w", pady=(3, 10))

        protocol = ttk.LabelFrame(container, text="Ultrasound-matched timing", padding=5)
        protocol.pack(fill="x", pady=5)
        self._field(protocol, 0, 0, "PRF (Hz)", "pulse_repetition_frequency_hz")
        self._field(protocol, 0, 1, "Pulse duration (ms)", "pulse_duration_ms")
        self._field(protocol, 1, 0, "Sonication (s)", "stimulation_duration_s")
        self._field(protocol, 1, 1, "Ultrasound carrier (kHz)", "ultrasound_frequency_khz")
        self._field(protocol, 2, 0, "Pre-mask (s)", "pre_mask_s")
        self._field(protocol, 2, 1, "Post-mask (s)", "post_mask_s")

        sound = ttk.LabelFrame(container, text="Auditory matching and background", padding=5)
        sound.pack(fill="x", pady=5)
        self._field(sound, 0, 0, "Audible carrier (Hz)", "audio_carrier_hz")
        self._field(sound, 0, 1, "Sample rate (Hz)", "sample_rate_hz")
        self._combo(sound, 1, 0, "Playback mode", "playback_mode", PLAYBACK_MODES)
        self._combo(sound, 1, 1, "Background", "background_type", BACKGROUND_TYPES)
        self._field(sound, 2, 0, "Matching gain (0–1)", "matching_gain")
        self._field(sound, 2, 1, "Background gain (0–1)", "background_gain")
        self._field(sound, 3, 0, "Master gain (0–1)", "master_gain")
        self._field(sound, 3, 1, "Stereo pan (-1 to 1)", "stereo_pan")
        self._field(sound, 4, 0, "Pulse ramp (ms)", "pulse_ramp_ms")
        self._field(sound, 4, 1, "Frozen random seed", "random_seed")

        safety = ttk.LabelFrame(container, text="Output, calibration, and allocation", padding=7)
        safety.pack(fill="x", pady=5)
        self._field(safety, 0, 0, "Output device index", "audio_device")
        self._combo(safety, 0, 1, "Session condition", "condition", ("sham", "active"))
        self.calibrated = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            safety,
            text=(
                "Headphones have been tested, actual SPL measured, and the protocol approved"
            ),
            variable=self.calibrated,
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=8, pady=6)
        ttk.Label(
            safety,
            text=(
                "The condition selector is for unblinded setup. A genuinely double-blind "
                "study requires a separately controlled allocation schedule."
            ),
            wraplength=760,
            foreground="#7a4200",
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=8, pady=4)

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=10)
        for label, callback in (
            ("List headphones", self.list_devices),
            ("Generate", self.generate),
            ("Play preview", self.preview),
            ("Stop preview", self.stop_preview),
            ("Save WAV", self.export),
            ("Save settings", self.save_settings),
        ):
            ttk.Button(controls, text=label, command=callback).pack(side="left", padx=3)
        self.run_button = ttk.Button(controls, text="Run session", command=self.run_session)
        self.run_button.pack(side="right", padx=3)

        self.status = tk.Text(container, height=12, wrap="word", state="disabled")
        self.status.pack(fill="both", expand=True, pady=(2, 0))
        self._message("Default condition is sham. No ultrasound is emitted during sham.")
        self._message(f"Configuration file: {CONFIG_PATH}")

    def _load_values(self):
        data = self.config.to_dict()
        for key, variable in self.variables.items():
            if key == "condition":
                variable.set("sham")
            else:
                value = data.get(key)
                variable.set("" if value is None else str(value))
        self.calibrated.set(self.config.headphones_calibrated)

    def _collect_config(self):
        data = self.config.to_dict()
        for name in (
            "pulse_repetition_frequency_hz",
            "pulse_duration_ms",
            "stimulation_duration_s",
            "ultrasound_frequency_khz",
            "pre_mask_s",
            "post_mask_s",
            "audio_carrier_hz",
            "matching_gain",
            "background_gain",
            "master_gain",
            "stereo_pan",
            "pulse_ramp_ms",
        ):
            data[name] = float(self.variables[name].get().strip())
        for name in ("sample_rate_hz", "random_seed"):
            data[name] = int(self.variables[name].get().strip())
        for name in ("playback_mode", "background_type"):
            data[name] = self.variables[name].get()
        device = self.variables["audio_device"].get().strip()
        data["audio_device"] = int(device) if device else None
        data["headphones_calibrated"] = self.calibrated.get()
        return MaskingConfig(**data).validate()

    def _message(self, text):
        self.status.configure(state="normal")
        self.status.insert("end", text.rstrip() + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")

    def _consume_messages(self):
        while True:
            try:
                item = self.messages.get_nowait()
            except queue.Empty:
                break
            if item == "__SESSION_COMPLETE__":
                self.running_process = None
                self.run_button.configure(state="normal")
            else:
                self._message(item)
        self.root.after(150, self._consume_messages)

    def _guard(self, action):
        try:
            return action()
        except Exception as error:
            self._message(f"ERROR: {error}")
            messagebox.showerror("Auditory masking", str(error))
            return None

    def list_devices(self):
        def action():
            player = SoundDevicePlayer()
            devices = player.backend.query_devices()
            self._message("Available headphone/output devices:")
            for index, device in enumerate(devices):
                if int(device.get("max_output_channels", 0)) >= 2:
                    self._message(f"  {index}: {device['name']}")
        return self._guard(action)

    def generate(self):
        def action():
            self.config = self._collect_config()
            self.generated = generate_mask(self.config)
            self._message(
                f"Generated {self.generated.duration_s:.2f} s stereo mask, "
                f"{self.config.expected_pulses} matched pulses, peak "
                f"{self.generated.peak:.3f}."
            )
            self._message(f"Frozen audio SHA-256: {self.generated.audio_sha256}")
            return self.generated
        return self._guard(action)

    def preview(self):
        def action():
            generated = self.generate()
            if generated is None:
                return
            self.player = SoundDevicePlayer(output_device=generated.config.audio_device)
            device = self.player.check_output(generated.sample_rate_hz)
            self.player.play(generated)
            self._message(f"Preview playing through: {device.get('name', 'selected device')}")
        return self._guard(action)

    def stop_preview(self):
        def action():
            if self.player is not None:
                self.player.stop()
            self._message("Audio preview stopped.")
        return self._guard(action)

    def export(self):
        def action():
            generated = self.generate()
            if generated is None:
                return
            destination = filedialog.asksaveasfilename(
                title="Save frozen masking waveform",
                defaultextension=".wav",
                initialfile="pmErC_5Hz_20ms_90s_frozen_mask.wav",
                filetypes=[("WAV audio", "*.wav")],
            )
            if destination:
                wav_path, metadata_path = save_mask(generated, destination)
                self._message(f"Saved WAV: {wav_path}")
                self._message(f"Saved metadata: {metadata_path}")
        return self._guard(action)

    def save_settings(self):
        def action():
            self.config = self._collect_config()
            self.config.to_json(CONFIG_PATH)
            self._message(f"Saved masking settings: {CONFIG_PATH}")
            return self.config
        return self._guard(action)

    def run_session(self):
        def action():
            if self.running_process is not None:
                raise RuntimeError("A stimulation session is already running.")
            config = self.save_settings()
            if config is None:
                return
            if config.enabled and not config.headphones_calibrated:
                raise RuntimeError("Confirm headphone testing, SPL calibration, and approval first.")
            condition = self.variables["condition"].get()
            if condition == "active" and not messagebox.askyesno(
                "Confirm active ultrasound",
                "ACTIVE mode will energize the IGT transducer. Confirm coupling, "
                "targeting, calibration, approved exposure, and emergency-stop readiness.",
            ):
                self._message("Active session was not started.")
                return
            self.stop_preview()
            environment = os.environ.copy()
            environment["FUS_SESSION_CONDITION"] = condition
            self.running_process = subprocess.Popen(
                [sys.executable, "-u", str(RUNNER_PATH)],
                cwd=str(SCRIPT_DIRECTORY.parent),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.run_button.configure(state="disabled")
            self._message(f"Starting {condition} session with the frozen mask configuration.")

            def read_output():
                try:
                    for line in self.running_process.stdout:
                        self.messages.put(line.rstrip())
                    return_code = self.running_process.wait()
                    self.messages.put(f"Session process exited with status {return_code}.")
                finally:
                    self.messages.put("__SESSION_COMPLETE__")

            threading.Thread(target=read_output, daemon=True).start()
        return self._guard(action)


def main():
    root = tk.Tk()
    AuditoryMaskingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
