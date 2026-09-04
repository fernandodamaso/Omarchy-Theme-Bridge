from __future__ import annotations

from enum import StrEnum


class ThemeErrorCode(StrEnum):
    THEME_NOT_FOUND = "THEME_NOT_FOUND"
    THEME_INVALID = "THEME_INVALID"
    THEME_UNSUPPORTED_COLOR = "THEME_UNSUPPORTED_COLOR"
    CALLER_FORBIDDEN = "CALLER_FORBIDDEN"
    PROTOCOL_MISMATCH = "PROTOCOL_MISMATCH"


class ThemeLoadError(RuntimeError):
    """A safe, bounded active-theme load failure."""

    def __init__(self, code: ThemeErrorCode | str) -> None:
        self.code = str(code)
        super().__init__(self.code)
