from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias, cast

from .color import ColorParseError, Rgba, contrast_ratio, from_oklch, mix, parse_css_color, relative_luminance, to_hex, to_oklch
from .errors import ThemeErrorCode, ThemeLoadError
from .theme_loader import ThemePaths, read_theme_name

NormalizedTheme: TypeAlias = dict[str, object]
CANONICAL_COLOR_RE = __import__("re").compile(r"^#[0-9a-f]{6}(?:[0-9a-f]{2})?$")

CANONICAL_ALIASES: dict[str, tuple[str, ...]] = {
    "background": ("background", "bg", "color0"),
    "dark_background": ("dark_background", "dark_bg"),
    "darker_background": ("darker_background", "darker_bg"),
    "lighter_background": ("lighter_background", "lighter_bg"),
    "foreground": ("foreground", "fg", "color7"),
    "dark_foreground": ("dark_foreground", "dark_fg"),
    "light_foreground": ("light_foreground", "light_fg"),
    "bright_foreground": ("bright_foreground", "bright_fg"),
    "red": ("red", "color1"),
    "green": ("green", "color2"),
    "yellow": ("yellow", "color3"),
    "blue": ("blue", "color4"),
    "magenta": ("magenta", "purple", "color5"),
    "cyan": ("cyan", "color6"),
    "accent": ("accent",),
    "selection": ("selection",),
    "muted": ("muted", "color8"),
}

SEMANTIC_KEYS = {
    "canvas",
    "surface",
    "surfaceRaised",
    "surfaceInset",
    "text",
    "textStrong",
    "textMuted",
    "border",
    "accent",
    "selection",
    "danger",
    "success",
    "warning",
    "info",
    "magenta",
    "cyan",
}
SOURCE_REQUIRED = {"background", "foreground"}
SOURCE_OPTIONAL = {
    "darkBackground",
    "darkerBackground",
    "lighterBackground",
    "darkForeground",
    "lightForeground",
    "brightForeground",
}


def _load_toml(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as stream:
            value = tomllib.load(stream)
    except FileNotFoundError as exc:
        raise ThemeLoadError(ThemeErrorCode.THEME_NOT_FOUND) from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID) from exc
    if not isinstance(value, dict):
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    return cast(dict[str, object], value)


def _resolve_raw(raw: Mapping[str, object], canonical: str) -> str | None:
    for key in CANONICAL_ALIASES[canonical]:
        value = raw.get(key)
        if value is not None:
            if not isinstance(value, str):
                raise ThemeLoadError(ThemeErrorCode.THEME_UNSUPPORTED_COLOR)
            return value
    return None


def _resolve_color(raw: Mapping[str, object], canonical: str, required: bool = False) -> Rgba | None:
    value = _resolve_raw(raw, canonical)
    if value is None:
        if required:
            raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
        return None
    try:
        return parse_css_color(value)
    except ColorParseError as exc:
        raise ThemeLoadError(ThemeErrorCode.THEME_UNSUPPORTED_COLOR) from exc


def _mode(raw: Mapping[str, object], paths: ThemePaths, background: Rgba) -> str:
    value = raw.get("mode")
    if value in {"dark", "light"}:
        return cast(str, value)
    legacy = raw.get("theme_type")
    if legacy in {"dark", "light"}:
        return cast(str, legacy)
    if paths.light_marker.is_file():
        return "light"
    return "light" if background.r + background.g + background.b > 382 else "dark"


def _derived_semantic(accent: Rgba, canvas: Rgba, hue: float) -> Rgba:
    lightness, chroma, _ = to_oklch(accent)
    target = from_oklch(lightness, max(0.11, min(0.20, chroma)), hue, accent.a)
    if contrast_ratio(target, canvas) >= 3.0:
        return target
    canvas_l, _, _ = to_oklch(canvas)
    direction = -1 if canvas_l > 0.55 else 1
    for step in range(1, 9):
        candidate_l = max(0.25, min(0.9, lightness + direction * step * 0.05))
        candidate = from_oklch(candidate_l, max(0.10, min(0.18, chroma)), hue, accent.a)
        if contrast_ratio(candidate, canvas) >= 3.0:
            return candidate
    return target


def _source_value(color: Rgba | None) -> str | None:
    return to_hex(color) if color is not None else None


def load_and_normalize(paths: ThemePaths) -> NormalizedTheme:
    raw = _load_toml(paths.colors_file)
    background = cast(Rgba, _resolve_color(raw, "background", required=True))
    foreground = cast(Rgba, _resolve_color(raw, "foreground", required=True))
    mode = _mode(raw, paths, background)

    dark_background = _resolve_color(raw, "dark_background")
    darker_background = _resolve_color(raw, "darker_background")
    lighter_background = _resolve_color(raw, "lighter_background")
    dark_foreground = _resolve_color(raw, "dark_foreground")
    light_foreground = _resolve_color(raw, "light_foreground")
    bright_foreground = _resolve_color(raw, "bright_foreground")
    muted = _resolve_color(raw, "muted")
    accent = _resolve_color(raw, "accent") or _resolve_color(raw, "blue") or mix(foreground, background, 0.2)

    surface_raised = lighter_background or mix(background, foreground, 0.12)
    surface = mix(background, surface_raised, 0.06) if lighter_background else mix(background, foreground, 0.07)

    canvas_distance = abs(relative_luminance(background) - relative_luminance(foreground))
    variants = [candidate for candidate in (dark_background, darker_background) if candidate is not None]
    farther = [candidate for candidate in variants if abs(relative_luminance(candidate) - relative_luminance(foreground)) > canvas_distance]
    if farther:
        surface_inset = max(farther, key=lambda color: abs(relative_luminance(color) - relative_luminance(foreground)))
    else:
        terminal = Rgba(0, 0, 0) if mode == "dark" else Rgba(255, 255, 255)
        surface_inset = mix(background, terminal, 0.10)

    text_strong = bright_foreground or light_foreground or mix(
        foreground,
        Rgba(255, 255, 255) if mode == "dark" else Rgba(0, 0, 0),
        0.18,
    )
    text_muted = dark_foreground or muted or mix(foreground, background, 0.42)
    border = muted or mix(foreground, background, 0.72)
    selection = _resolve_color(raw, "selection") or mix(accent, background, 0.68)

    named = {
        "danger": _resolve_color(raw, "red") or _derived_semantic(accent, background, 25),
        "success": _resolve_color(raw, "green") or _derived_semantic(accent, background, 145),
        "warning": _resolve_color(raw, "yellow") or _derived_semantic(accent, background, 85),
        "info": _resolve_color(raw, "blue") or _derived_semantic(accent, background, 265),
        "magenta": _resolve_color(raw, "magenta") or _derived_semantic(accent, background, 320),
        "cyan": _resolve_color(raw, "cyan") or _derived_semantic(accent, background, 205),
    }

    colors: dict[str, str] = {
        "canvas": to_hex(background),
        "surface": to_hex(surface),
        "surfaceRaised": to_hex(surface_raised),
        "surfaceInset": to_hex(surface_inset),
        "text": to_hex(foreground),
        "textStrong": to_hex(text_strong),
        "textMuted": to_hex(text_muted),
        "border": to_hex(border),
        "accent": to_hex(accent),
        "selection": to_hex(selection),
        **{key: to_hex(value) for key, value in named.items()},
    }

    source_candidates = {
        "background": background,
        "darkBackground": dark_background,
        "darkerBackground": darker_background,
        "lighterBackground": lighter_background,
        "foreground": foreground,
        "darkForeground": dark_foreground,
        "lightForeground": light_foreground,
        "brightForeground": bright_foreground,
    }
    source = {
        key: cast(str, _source_value(value))
        for key, value in source_candidates.items()
        if value is not None
    }

    payload: NormalizedTheme = {
        "schemaVersion": 1,
        "name": read_theme_name(paths),
        "mode": mode,
        "colors": colors,
        "source": source,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload["generation"] = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
    return validate_normalized_theme(payload)


def validate_normalized_theme(value: object) -> NormalizedTheme:
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "generation", "name", "mode", "colors", "source"}:
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    if value.get("schemaVersion") != 1 or value.get("mode") not in {"dark", "light"}:
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    name = value.get("name")
    generation = value.get("generation")
    if not isinstance(name, str) or not 1 <= len(name) <= 128:
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    if not isinstance(generation, str) or not __import__("re").fullmatch(r"sha256:[0-9a-f]{64}", generation):
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    colors = value.get("colors")
    source = value.get("source")
    if not isinstance(colors, dict) or set(colors) != SEMANTIC_KEYS:
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    if not all(isinstance(color, str) and CANONICAL_COLOR_RE.fullmatch(color) for color in colors.values()):
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    if not isinstance(source, dict) or not SOURCE_REQUIRED.issubset(source) or not set(source).issubset(SOURCE_REQUIRED | SOURCE_OPTIONAL):
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    if not all(isinstance(color, str) and CANONICAL_COLOR_RE.fullmatch(color) for color in source.values()):
        raise ThemeLoadError(ThemeErrorCode.THEME_INVALID)
    return cast(NormalizedTheme, value)
