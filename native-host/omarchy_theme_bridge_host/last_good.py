from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from . import MAX_MESSAGE_BYTES
from .errors import ThemeLoadError
from .theme_normalizer import NormalizedTheme, validate_normalized_theme


class SnapshotError(RuntimeError):
    pass


class LastGoodStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> NormalizedTheme | None:
        try:
            raw = self.path.read_bytes()
            if len(raw) > MAX_MESSAGE_BYTES:
                return None
            value = json.loads(raw.decode("utf-8"))
            return validate_normalized_theme(value)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ThemeLoadError):
            return None

    def save(self, theme: Mapping[str, object]) -> None:
        try:
            validated = validate_normalized_theme(dict(theme))
        except ThemeLoadError as exc:
            raise SnapshotError("Snapshot is invalid") from exc
        payload = (json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if len(payload) > MAX_MESSAGE_BYTES:
            raise SnapshotError("Snapshot exceeds size limit")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
