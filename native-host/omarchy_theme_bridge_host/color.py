from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

HEX_RE = re.compile(r"^#(?P<hex>[0-9a-fA-F]+)$")
RGB_RE = re.compile(r"^rgba?\((?P<body>.*)\)$", re.IGNORECASE)
NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
PERCENT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)%$")


class ColorParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Rgba:
    r: int
    g: int
    b: int
    a: int = 255

    def __post_init__(self) -> None:
        for value in (self.r, self.g, self.b, self.a):
            if not isinstance(value, int) or not 0 <= value <= 255:
                raise ValueError("Color channels must be bytes")


def _round_byte(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _decimal(token: str) -> Decimal:
    if not NUMBER_RE.fullmatch(token):
        raise ColorParseError("Invalid numeric color channel")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise ColorParseError("Invalid numeric color channel") from exc
    if not value.is_finite():
        raise ColorParseError("Invalid numeric color channel")
    return value


def _parse_rgb_channel(token: str) -> int:
    token = token.strip()
    if PERCENT_RE.fullmatch(token):
        value = _decimal(token[:-1])
        if value < 0 or value > 100:
            raise ColorParseError("RGB percentage is out of range")
        return _round_byte(value * Decimal(255) / Decimal(100))
    value = _decimal(token)
    if value < 0 or value > 255:
        raise ColorParseError("RGB channel is out of range")
    return _round_byte(value)


def _parse_alpha(token: str) -> int:
    token = token.strip()
    if PERCENT_RE.fullmatch(token):
        value = _decimal(token[:-1])
        if value < 0 or value > 100:
            raise ColorParseError("Alpha percentage is out of range")
        return _round_byte(value * Decimal(255) / Decimal(100))
    value = _decimal(token)
    if value < 0 or value > 1:
        raise ColorParseError("Alpha channel is out of range")
    return _round_byte(value * Decimal(255))


def _parse_hex(value: str) -> Rgba:
    match = HEX_RE.fullmatch(value)
    if not match:
        raise ColorParseError("Invalid hex color")
    raw = match.group("hex")
    if len(raw) not in {3, 4, 6, 8}:
        raise ColorParseError("Invalid hex color length")
    if len(raw) in {3, 4}:
        raw = "".join(char * 2 for char in raw)
    if len(raw) == 6:
        raw += "ff"
    return Rgba(*(int(raw[index:index + 2], 16) for index in range(0, 8, 2)))


def _parse_rgb_function(value: str) -> Rgba:
    match = RGB_RE.fullmatch(value)
    if not match:
        raise ColorParseError("Unsupported color syntax")
    body = match.group("body").strip()
    if not body:
        raise ColorParseError("Empty RGB function")

    alpha_token: str | None = None
    if "/" in body:
        if body.count("/") != 1:
            raise ColorParseError("Invalid alpha separator")
        body, alpha_token = (part.strip() for part in body.split("/", 1))
        if not alpha_token:
            raise ColorParseError("Missing alpha channel")

    if "," in body:
        if any(character.isspace() for character in body.replace(",", "")):
            # Whitespace around comma tokens is valid; mixed delimiter means a
            # comma-separated segment contains multiple whitespace tokens.
            pass
        parts = [part.strip() for part in body.split(",")]
        if len(parts) == 4 and alpha_token is None:
            alpha_token = parts.pop()
        if len(parts) != 3 or any(not part or len(part.split()) != 1 for part in parts):
            raise ColorParseError("Invalid comma RGB syntax")
    else:
        parts = body.split()
        if len(parts) != 3:
            raise ColorParseError("Invalid space RGB syntax")

    channels = [_parse_rgb_channel(part) for part in parts]
    alpha = 255 if alpha_token is None else _parse_alpha(alpha_token)
    return Rgba(*channels, alpha)


def parse_css_color(value: str) -> Rgba:
    if not isinstance(value, str):
        raise ColorParseError("Color must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > 128:
        raise ColorParseError("Color is empty or too long")
    if normalized.startswith("#"):
        return _parse_hex(normalized)
    return _parse_rgb_function(normalized)


def to_hex(color: Rgba) -> str:
    base = f"#{color.r:02x}{color.g:02x}{color.b:02x}"
    return base if color.a == 255 else f"{base}{color.a:02x}"


def mix(start: Rgba, end: Rgba, amount: float) -> Rgba:
    if not math.isfinite(amount) or not 0 <= amount <= 1:
        raise ValueError("Mix amount must be between zero and one")
    factor = Decimal(str(amount))
    inverse = Decimal(1) - factor
    return Rgba(*(
        _round_byte(Decimal(left) * inverse + Decimal(right) * factor)
        for left, right in zip(
            (start.r, start.g, start.b, start.a),
            (end.r, end.g, end.b, end.a),
            strict=True,
        )
    ))


def _linear_channel(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(color: Rgba) -> float:
    return 0.2126 * _linear_channel(color.r) + 0.7152 * _linear_channel(color.g) + 0.0722 * _linear_channel(color.b)


def contrast_ratio(first: Rgba, second: Rgba) -> float:
    light, dark = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def to_oklch(color: Rgba) -> tuple[float, float, float]:
    r = _linear_channel(color.r)
    g = _linear_channel(color.g)
    b = _linear_channel(color.b)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_ = math.copysign(abs(l) ** (1 / 3), l)
    m_ = math.copysign(abs(m) ** (1 / 3), m)
    s_ = math.copysign(abs(s) ** (1 / 3), s)
    okl = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    oka = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    okb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    chroma = math.hypot(oka, okb)
    hue = math.degrees(math.atan2(okb, oka)) % 360 if chroma > 1e-9 else 0.0
    return okl, chroma, hue


def _srgb_channel(linear: float) -> float:
    return 12.92 * linear if linear <= 0.0031308 else 1.055 * (linear ** (1 / 2.4)) - 0.055


def from_oklch(lightness: float, chroma: float, hue: float, alpha: int = 255) -> Rgba:
    angle = math.radians(hue)
    oka = chroma * math.cos(angle)
    okb = chroma * math.sin(angle)
    l_ = lightness + 0.3963377774 * oka + 0.2158037573 * okb
    m_ = lightness - 0.1055613458 * oka - 0.0638541728 * okb
    s_ = lightness - 0.0894841775 * oka - 1.2914855480 * okb
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3
    linear = (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )
    channels = [
        _round_byte(Decimal(str(max(0.0, min(1.0, _srgb_channel(channel))) * 255)))
        for channel in linear
    ]
    return Rgba(*channels, alpha)
