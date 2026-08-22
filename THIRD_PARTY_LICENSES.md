# Third-party licensing and attribution

The integrated Dortmund auditory-masking adaptation, its protocol orchestration,
graphical workflow, and project-specific documentation are attributed to
**Apochi Obed and Nikolai Axmacher**. Cite this adaptation as:

> Apochi, O., & Axmacher, N. (2026). *Focused Ultrasound Driving System with Synchronized
> Auditory Masking for Active and Sham Entorhinal Cortex Stimulation*
> (Version 1.0.0) [Computer software].
> https://github.com/Obediko/fus-driving-system-auditory-masking

Authorship of the adaptation does not transfer ownership of its upstream
dependencies or remove their independent licensing and citation obligations.

The original Radboud FUS Driving System remains governed by its root `LICENSE`
(MIT), with copyright retained by Margely Cornelissen, Stein Fekkes, and Erik
Dumont.

The following bundled component is **not MIT-licensed**:

`fus_ds_package/fus_driving_systems/auditory_masking/_vendor/`

That directory contains adapted code from:

> Hira Musarrat and Benjamin Kop. *Auditory Mask Generator – NeuroFUS Edition*.
> https://github.com/hiramusarrat8-beep/auditory-mask-generator-tpo
> DOI: https://doi.org/10.5281/zenodo.20681923

Its copyright remains with Benjamin Kop and Hira Musarrat. The complete
research-only license and EULA are distributed unmodified alongside the adapted
files:

- `fus_ds_package/fus_driving_systems/auditory_masking/_vendor/LICENSE`
- `fus_ds_package/fus_driving_systems/auditory_masking/_vendor/EULA.md`
- `fus_ds_package/fus_driving_systems/auditory_masking/_vendor/NOTICE.md`

Use, modification, and redistribution of the vendor-derived component are
limited to non-commercial research and education. Cite the software in any
publication, presentation, poster, grant application, or other public output
informed by its use. Do not represent the combined distribution as entirely
MIT-licensed or use the restricted components in commercial products without
the original authors' written permission.

The proprietary NeuroFUS SDK and its device-control components are not included.
IGT stimulation continues to use the existing Radboud/IGT driver and its
configured Dortmund equipment files.
