from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ThemePaths:
    theme_dir: Path
    colors_file: Path
    name_file: Path
    light_marker: Path

    @classmethod
    def from_theme_dir(cls, theme_dir: Path) -> "ThemePaths":
        directory = theme_dir.expanduser().resolve()
        return cls(
            theme_dir=directory,
            colors_file=directory / "colors.toml",
            name_file=directory / "theme.name",
            light_marker=directory / "light.mode",
        )

    @classmethod
    def resolve(cls, home: Path, override: str | None) -> "ThemePaths":
        if override:
            return cls.from_theme_dir(Path(override))
        current = home / ".local" / "state" / "omarchy" / "current"
        return cls(
            theme_dir=current / "theme",
            colors_file=current / "theme" / "colors.toml",
            name_file=current / "theme.name",
            light_marker=current / "theme" / "light.mode",
        )


def read_theme_name(paths: ThemePaths) -> str:
    try:
        raw = paths.name_file.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        raw = paths.theme_dir.name
    if not raw:
        raw = "Omarchy Theme"
    normalized = raw.replace("_", " ").replace("-", " ")
    if raw == normalized.lower() or raw == normalized:
        normalized = normalized.title()
    return normalized[:128]
