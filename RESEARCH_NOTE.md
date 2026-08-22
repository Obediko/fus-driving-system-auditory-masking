# Protocol-synchronized auditory masking for active and sham focused ultrasound stimulation of the human posterior-medial entorhinal cortex

**Authors:** Apochi Obed and Nikolai Axmacher  
**Affiliation:** Ruhr University Bochum, Bochum, Germany  
**Software version:** 1.0.0  
**Repository:** https://github.com/Obediko/fus-driving-system-auditory-masking

## Abstract

Low-intensity transcranial ultrasound stimulation can produce audible signals
and indirect auditory activation that complicate interpretation of active and
sham comparisons. This research software integrates reproducible headphone
masking with an Image Guided Therapy D054 focused-ultrasound driving system for
a posterior-medial entorhinal cortex protocol. The reference configuration
uses a 300 kHz ultrasound carrier, 5 Hz pulse repetition frequency, 20 ms pulse
duration, and 90 s stimulation, corresponding to 450 pulses and a 10% duty
cycle. A deterministic stereo masking waveform spans the stimulation period
with one-second pre-stimulation and post-stimulation intervals. Active sessions
execute the existing ultrasound sequence after audio playback begins, whereas
sham sessions reproduce the same waveform without connecting to or energizing
the generator. Automated tests verify timing, reproducibility, non-energizing
sham behavior, calibration gates, and failure handling. This document describes
software behavior; it does not establish clinical safety, target engagement,
effective participant blinding, or hardware-measured synchronization.

**Keywords:** focused ultrasound; transcranial ultrasound stimulation; auditory
confound; sham control; entorhinal cortex; spatial navigation.

## Introduction

Transcranial ultrasound stimulation offers a route to investigating cortical
and deep brain systems with spatially focused acoustic energy. Human studies
have reported changes in functional connectivity and neurochemical measures
after stimulation of deep cortical targets, although such effects depend on the
specific protocol, anatomy, and measurement conditions [1]. The posterior-medial
entorhinal cortex is of particular interest because human neuroimaging studies
distinguish posterior-medial and anterior-lateral entorhinal subdivisions with
different connectivity patterns and sensitivity to spatial information [2,3].

A central methodological problem is that pulsed ultrasound may activate
auditory pathways or produce detectable airborne or bone-conducted sound.
Animal studies demonstrated that apparently widespread ultrasound-related
activity can arise through indirect auditory or cochlear mechanisms [4,5]. In
humans, Braun and colleagues reported that an appropriately matched auditory
signal reduced detection of stimulation to chance and eliminated an associated
auditory electroencephalographic response in their experimental setting [6].
Other work has examined complex masking sounds, including auditory Mondrian
stimuli, for airborne acoustic artifacts [7]. These findings justify explicit
auditory control, but do not establish that one masking waveform eliminates
every source of sensory unblinding under every protocol.

This project implements a reproducible masking and active/sham control layer
for a specific IGT-based entorhinal stimulation workflow. The scientific
objective is to make the auditory exposure more comparable between conditions
while preserving the original ultrasound driver's control over stimulation.

## Materials and methods

### Hardware and stimulation protocol

The implementation targets the Image Guided Therapy D054 driving system and the
Imasonic `IS_PCD15287_01005` ten-element transducer using the Dortmund IGT
configuration. The ultrasound carrier frequency is 300 kHz. Pulses are
delivered at 5 Hz for 90 s, with each pulse lasting 20 ms. The corresponding
pulse repetition interval is 200 ms, the duty cycle is 10%, and the total pulse
count is 450. Generator output amplitude, pressure, equalization, transducer
placement, acoustic coupling, and participant-specific transmission are not
determined by these timing values and require separate measurement and review.

### Auditory waveform generation

The auditory waveform is generated from a fixed random seed and configurable
masking parameters. By default, an audible carrier is gated according to the
5 Hz, 20 ms stimulation envelope and combined with a broadband noise
background. The audio is sampled at 44.1 kHz and presented in stereo. One
second of masking precedes the stimulation window and one second follows it,
producing a total waveform duration of 92 s. The 300 kHz ultrasound carrier is
not reproduced by the headphone output.

Generated waveforms can be saved as frozen WAV files with accompanying JSON
metadata and a SHA-256 digest. Fixed configuration and random seed allow the
same digital waveform to be reproduced across active and sham sessions.
Digital amplitude does not determine sound-pressure level at the ear, so
headphone output must be independently calibrated.

### Active and sham conditions

For the active condition, the software initializes the existing IGT driver,
connects to the configured generator, and buffers the approved ultrasound
sequence. It then verifies the audio output, starts masking, waits for the
pre-mask interval, and calls the driver's `execute_sequence()` method once.
The IGT generator remains responsible for delivering the programmed pulse
train.

For the sham condition, the same frozen auditory waveform is presented for the
same duration. The implementation does not connect to the generator, buffer an
active sequence, or execute ultrasound. This establishes equivalence of the
digital audio stimulus, not equivalence of all sensory, mechanical, visual, or
operator-related cues.

### Safety controls and reproducibility

Execution is blocked when headphone calibration has not been acknowledged,
when the requested audio output cannot start, or when waveform timing differs
from the configured ultrasound protocol. External-triggered sequences are
rejected because an independent software audio clock cannot establish the
physical onset of an uncontrolled hardware trigger. If an active sequence
fails, masking is stopped and the established generator-disconnection pathway
is retained.

The repository includes 19 hardware-independent regression tests covering pulse
timing, deterministic waveform generation, active/sham audio equivalence,
non-energizing sham execution, integrity checks, unavailable headphone output,
calibration gates, trigger restrictions, and failure cleanup. These tests use
simulated components and must not be represented as verification of physical
ultrasound delivery or participant safety.

## Interpretation and limitations

The system improves experimental control by coupling masking generation to a
predefined stimulation protocol and preventing accidental ultrasound delivery
in the sham pathway. Its current reference runner is intentionally restricted
to the Dortmund configuration; changing the stimulation protocol requires the
ultrasound sequence and masking settings to be updated together.

Several limitations remain. First, software-reported output latency does not
prove the true temporal relationship between headphone sound and acoustic
ultrasound onset. Millisecond-level synchronization requires independent
measurement. Second, matched headphone audio cannot guarantee cancellation of
bone-conducted sound, transducer vibration, generator noise, or tactile cues.
Participant discrimination should therefore be tested empirically. Third, the
visible condition selector is not a concealed randomization system and does not
establish double blinding. Fourth, protocol timing does not establish acoustic
pressure, mechanical index, thermal exposure, target engagement, or efficacy.
Those quantities require individualized planning and protocol-specific
assessment consistent with current TUS reporting and safety guidance [8-10].

The work is provided as research software. It should not be described as a
validated medical device, an independently established treatment, or evidence
that the posterior-medial entorhinal cortex has been successfully stimulated.

## Authorship and software provenance

**Apochi Obed and Nikolai Axmacher** are the authors of this project-specific
Dortmund adaptation and its accompanying research documentation. The adaptation
includes the integrated active/sham session workflow, entorhinal stimulation
protocol, reproducible masking controls, and project-specific documentation.

The original Radboud FUS Driving System was developed by Margely Cornelissen,
Stein Fekkes, and Erik Dumont. Auditory signal-generation components were
adapted from separately authored software by Hira Musarrat and Benjamin Kop.
These upstream contributions remain subject to their respective copyright,
licensing, and citation requirements [11,12].

## Recommended citation

Apochi, O., & Axmacher, N. (2026). *Focused Ultrasound Driving System with Synchronized Auditory
Masking for Active and Sham Entorhinal Cortex Stimulation* (Version 1.0.0)
[Computer software]. https://github.com/Obediko/fus-driving-system-auditory-masking

## References

1. Yaakub, S. N., White, T. A., Roberts, J., Martin, E., Verhagen, L., Stagg,
   C. J., Hall, S., & Fouragnan, E. F. (2023). Transcranial focused
   ultrasound-mediated neurochemical and functional connectivity changes in
   deep cortical regions in humans. *Nature Communications, 14*, 5318.
   https://doi.org/10.1038/s41467-023-40998-0

2. Maass, A., Berron, D., Libby, L. A., Ranganath, C., & Düzel, E. (2015).
   Functional subregions of the human entorhinal cortex. *eLife, 4*, e06426.
   https://doi.org/10.7554/eLife.06426

3. Navarro Schröder, T., Haak, K. V., Zaragoza Jimenez, N. I., Beckmann, C. F.,
   & Doeller, C. F. (2015). Functional topography of the human entorhinal
   cortex. *eLife, 4*, e06738. https://doi.org/10.7554/eLife.06738

4. Sato, T., Shapiro, M. G., & Tsao, D. Y. (2018). Ultrasonic neuromodulation
   causes widespread cortical activation via an indirect auditory mechanism.
   *Neuron, 98*(5), 1031-1041.e5.
   https://doi.org/10.1016/j.neuron.2018.05.009

5. Guo, H., Hamilton, M., Offutt, S. J., Gloeckner, C. D., Li, T., Kim, Y.,
   Legon, W., Alford, J. K., & Lim, H. H. (2018). Ultrasound produces extensive
   brain activation via a cochlear pathway. *Neuron, 98*(5), 1020-1030.e4.
   https://doi.org/10.1016/j.neuron.2018.04.036

6. Braun, V., Blackmore, J., Cleveland, R. O., & Butler, C. R. (2020).
   Transcranial ultrasound stimulation in humans is associated with an
   auditory confound that can be effectively masked. *Brain Stimulation,
   13*(6), 1527-1534. https://doi.org/10.1016/j.brs.2020.08.014

7. Liang, W., Guo, H., Mittelstein, D. R., Shapiro, M. G., Shimojo, S., &
   Shehata, M. H. (2023). Auditory Mondrian masks the airborne-auditory
   artifact of focused ultrasound stimulation in humans. *Brain Stimulation,
   16*(2), 604-606.
   https://doi.org/10.1016/j.brs.2023.03.002

8. Martin, E., Aubry, J.-F., Schafer, M., Verhagen, L., Treeby, B., & Butts
   Pauly, K. (2024). ITRUSST consensus on standardised reporting for
   transcranial ultrasound stimulation. *Brain Stimulation, 17*(3), 607-615.
   https://doi.org/10.1016/j.brs.2024.04.013

9. Murphy, K. R., Nandi, T., Kop, B., Osada, T., Lueckel, M., N'Djin, W. A.,
   and colleagues (2025). A practical guide to transcranial ultrasonic
   stimulation from the IFCN-endorsed ITRUSST consortium. *Clinical
   Neurophysiology, 171*, 192-226.
   https://doi.org/10.1016/j.clinph.2025.01.004

10. Aubry, J.-F., Attali, D., Schafer, M. E., Fouragnan, E., Caskey, C. F.,
    and colleagues (2025). ITRUSST consensus on biophysical safety for
    transcranial ultrasound stimulation. *Brain Stimulation, 18*(6),
    1896-1905. https://doi.org/10.1016/j.brs.2025.10.007

11. Cornelissen, M., Fekkes, S., & Dumont, E. (2024-2025). *Radboud FUS
    Driving System Software* (Version 2.2) [Computer software].
    https://github.com/Donders-Institute/Radboud-FUS-driving-system-software

12. Musarrat, H., & Kop, B. (2026). *Auditory Mask Generator: NeuroFUS
    Edition* [Computer software]. https://doi.org/10.5281/zenodo.20681923
