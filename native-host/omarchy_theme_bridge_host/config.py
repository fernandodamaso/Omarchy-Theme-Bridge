from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ORIGIN_RE = re.compile(r"^chrome-extension://[a-p]{32}/$")


class ConfigError(RuntimeError):
    """Installed host configuration is missing or invalid."""


class CallerForbidden(ConfigError):
    """Chrome launched the host for an unexpected extension origin."""


@dataclass(frozen=True, slots=True)
class HostConfig:
    allowed_origin: str

    @classmethod
    def load(cls, path: Path) -> "HostConfig":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError("Host configuration is invalid") from exc
        if not isinstance(value, dict) or set(value) != {"allowedOrigin"}:
            raise ConfigError("Host configuration has unexpected fields")
        origin = value["allowedOrigin"]
        if not isinstance(origin, str) or not ORIGIN_RE.fullmatch(origin):
            raise ConfigError("Allowed origin is invalid")
        return cls(allowed_origin=origin)

    def assert_caller(self, argv: Sequence[str]) -> None:
        caller = argv[1] if len(argv) > 1 else ""
        if caller != self.allowed_origin:
            raise CallerForbidden("Caller origin is not allowed")
