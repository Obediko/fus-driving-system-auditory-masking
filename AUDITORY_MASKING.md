# Auditory masking for the Dortmund IGT pmErC protocol

This customization was developed by **Obed Apochi** for the Dortmund IGT D054
workflow. It adapts Hira Musarrat and Benjamin Kop's separately authored
auditory-mask generator for the existing Radboud FUS Driving System. It does
not use or emulate the NeuroFUS TPO hardware interface. Active ultrasound
remains under the original IGT D054 generator driver.

The primary citation for the integrated implementation is:

> Apochi, O. (2026). *Focused Ultrasound Driving System with Synchronized
> Auditory Masking for Active and Sham Entorhinal Cortex Stimulation*
> (Version 1.0.0) [Computer software].
> https://github.com/Obediko/fus-driving-system-auditory-masking

## Fixed protocol and default waveform

| Setting | Value |
| --- | --- |
| Driving-system profile | `IGT-32-ch_comb_1x10-ch_DORTMUND` |
| Generator | IGT D054 |
| Transducer | `IS_PCD15287_01005` |
| Ultrasound carrier | 300 kHz |
| Pulse repetition frequency | 5 Hz |
| Pulse duration | 20 ms |
| Pulse repetition interval | 200 ms |
| Duty cycle | 10% |
| Ultrasound duration | 90 s |
| Ultrasound pulses | 450 |
| Pre-mask interval | 1 s |
| Post-mask interval | 1 s |
| Total audio duration | 92 s |
| Audible carrier | 14,000 Hz, adjustable |
| Sample rate | 44,100 Hz |
| Default playback | Matched pulse envelope plus white-noise background |
| Default condition | Sham |
| Frozen random seed | `15287005` |

The 300 kHz ultrasound carrier is never sent to headphones. Headphone masking
uses an audible carrier gated by the 5 Hz, 20 ms pulse pattern. The carrier,
mask type, gain, lateralization, and other settings must be validated with the
actual transducer, headphones, and participants.

## Installation on the existing Windows system

Extract the delivered project so that the updated files replace their
counterparts in the existing project. The ZIP intentionally excludes `.git`,
so merging it into an existing checkout does not replace Git metadata.

In PowerShell:

```powershell
cd C:\Users\Neuro\FUS\Radboud-FUS-driving-system-software
& C:\Users\Neuro\Envs\FUS_DS_PACKAGE\Scripts\Activate.ps1
python -m pip install sounddevice
python -m pip install -e .\fus_ds_package
```

The existing installation already supplies NumPy, SciPy, and Tkinter. The
optional `colorednoise` package is not required because the adapter provides
a deterministic fallback for colored-noise generation.

## Launch the masking interface

```powershell
python .\standalone_driving_system_software\auditory_masking_gui.py
```

The interface provides:

- Editable pulse frequency, pulse duration, sonication duration, and padding.
- Matching-only, background-only, and combined audio modes.
- White, colored, narrowband, hybrid-ultrasound, and auditory-Mondrian masks.
- Audible carrier, gain, stereo pan, ramps, and deterministic random seed.
- Headphone/output-device listing and selection.
- Audio generation, preview, stop, and frozen WAV/JSON export.
- Explicit headphone-calibration confirmation.
- Sham and active execution of the existing pmErC IGT script.

The session selector is deliberately visible during setup. It does not create
a double-blind allocation by itself. A genuinely blinded experiment requires
a separately concealed randomization schedule and access-controlled assignment
workflow.

## Mandatory pre-session validation

1. Select and test the intended headphones.
2. Start with conservative system and headphone volume.
3. Measure actual headphone sound-pressure level with suitable equipment.
4. Confirm that the masking level, duration, and protocol are approved by the
   responsible institution and ethics process.
5. Determine whether participants can discriminate active from sham under the
   selected mask. Adjust or abandon the configuration if blinding fails.
6. Confirm transducer coupling, targeting, calibration, pressure, emergency-stop
   readiness, and all previously approved ultrasound safety limits.
7. Only then select the headphone-calibration checkbox and save settings.

By default, `headphones_calibrated` is `false`. Both active and sham execution
stop before stimulation until calibration has been explicitly confirmed.
Digital waveform amplitude is not an SPL measurement.

## Running the existing Spyder script

The dedicated protocol remains:

```text
standalone_driving_system_software/standalone_igt_pmErC.py
```

Open and run that script in Spyder after saving the masking configuration. Its
default condition is `sham`; sham playback never connects to, buffers, or
energizes the IGT generator.

To run an active condition from PowerShell:

```powershell
$env:FUS_SESSION_CONDITION = "active"
python .\standalone_driving_system_software\standalone_igt_pmErC.py
Remove-Item Env:\FUS_SESSION_CONDITION
```

Or launch the graphical interface, select `active`, and confirm the explicit
ultrasound safety prompt.

The configuration is stored in:

```text
standalone_driving_system_software/masking_config_pmErC.json
```

For participant work, use the same frozen configuration and random seed for
active and sham. The session exports a frozen stereo WAV, JSON metadata, a
SHA-256 audio fingerprint, and timestamped event logs to:

```text
C:\Temp\pmErC_auditory_masking\
```

The event log records the masking sequence without exposing the condition
label. The original IGT hardware logs remain subject to the existing driver
and institutional access controls.

## Synchronization and failure behavior

The IGT sequence is prepared normally. The audio stream is checked and started
once. The controller accounts for reported output latency, waits for the
configured pre-mask interval, and then calls `execute_sequence` exactly once.
The buffered generator controls all 450 ultrasound pulses. The sham pathway
waits for the same stimulation duration without calling the generator.

Ultrasound is not started if headphone playback fails or the stream is
inactive. If active execution raises an error, playback is stopped and the
existing `finally` block disconnects the generator. External-trigger mode is
rejected because an independent software audio clock cannot establish the
actual onset of an uncontrolled hardware trigger.

The reported audio onset is an estimate derived from the audio backend. For
millisecond-level claims, measure the real relationship between headphone
output and the IGT start signal using suitable hardware. This software does
not replace independent acoustic, electrical, or participant-safety testing.

## Hardware-free regression tests

```powershell
python -m unittest fus_driving_systems.tests.test_auditory_masking -v
```

The tests verify pulse timing, deterministic active/sham audio, frozen-file
integrity, non-energizing sham, playback failure, headphone-calibration gates,
external-trigger rejection, and generator-failure cleanup.

## Attribution and research-only terms

The original Radboud FUS driver remains MIT-licensed. Vendor-derived masking
components are restricted to non-commercial research and education under the
separate license and EULA in:

```text
fus_ds_package/fus_driving_systems/auditory_masking/_vendor/
```

Cite this integrated adaptation, the original Radboud driving software, and the
underlying masking software when each materially contributes to the reported
work. The upstream masking reference is:

Hira Musarrat and Benjamin Kop. *Auditory Mask Generator – NeuroFUS Edition*.
https://github.com/hiramusarrat8-beep/auditory-mask-generator-tpo.
https://doi.org/10.5281/zenodo.20681923.
