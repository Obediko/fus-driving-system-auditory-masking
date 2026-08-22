"""Research-only auditory masking for Radboud/IGT ultrasound sessions.

The vendor-derived components in ``_vendor`` are governed by their separate
research-only license and end-user agreement. The upstream FUS driver retains
its original MIT license.
"""

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
    "SoundDevicePlayer",
    "generate_mask",
    "load_mask",
    "save_mask",
]
