"""Research-only auditory masking for Radboud/IGT ultrasound sessions.

The vendor-derived components in ``_vendor`` are governed by their separate
research-only license and end-user agreement. The upstream FUS driver retains
its original MIT license.

Published adaptation: Apochi, O., and Axmacher, N. (2026).
https://doi.org/10.5281/zenodo.22059704
"""

from .citation import (
    SOFTWARE_AUTHORS,
    SOFTWARE_CITATION,
    SOFTWARE_DOI,
    SOFTWARE_DOI_URL,
    SOFTWARE_TITLE,
    SOFTWARE_VERSION,
    UPSTREAM_MASKING_AUTHORS,
    UPSTREAM_MASKING_DOI,
)
from .config import MaskingConfig
from .engine import (
    GeneratedMask,
    MaskingPlaybackError,
    SoundDevicePlayer,
    generate_mask,
    load_mask,
    save_mask,
)
from .session import MaskedIGTSession, SessionResult

__all__ = [
    "GeneratedMask",
    "MaskedIGTSession",
    "MaskingConfig",
    "MaskingPlaybackError",
    "SessionResult",
    "SOFTWARE_AUTHORS",
    "SOFTWARE_CITATION",
    "SOFTWARE_DOI",
    "SOFTWARE_DOI_URL",
    "SOFTWARE_TITLE",
    "SOFTWARE_VERSION",
    "SoundDevicePlayer",
    "UPSTREAM_MASKING_AUTHORS",
    "UPSTREAM_MASKING_DOI",
    "generate_mask",
    "load_mask",
    "save_mask",
]
