import pytest

from omarchy_theme_bridge_host.color import ColorParseError, mix, parse_css_color, relative_luminance, to_hex


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("#abc", "#aabbcc"),
        ("#abcd", "#aabbccdd"),
        ("#AABBCC", "#aabbcc"),
        ("rgb(122, 162, 247)", "#7aa2f7"),
        ("rgb(47.843% 63.529% 96.863% / 50%)", "#7aa2f780"),
        ("rgba(122 162 247 / .25)", "#7aa2f740"),
    ],
)
def test_parse_foundational_css_colors(source: str, expected: str) -> None:
    assert to_hex(parse_css_color(source)) == expected


@pytest.mark.parametrize(
    "source",
    [
        "color-mix(in oklch, red, blue)",
        "rgb(300 0 0)",
        "rgb(1, 2 3)",
        "var(--accent)",
        "red",
        "rgb(NaN 0 0)",
    ],
)
def test_rejects_unsupported_or_out_of_range_color(source: str) -> None:
    with pytest.raises(ColorParseError):
        parse_css_color(source)


def test_mix_is_deterministic_and_preserves_alpha() -> None:
    assert to_hex(mix(parse_css_color("#00000080"), parse_css_color("#ffffff"), 0.5)) == "#808080c0"


def test_relative_luminance_orders_black_before_white() -> None:
    assert relative_luminance(parse_css_color("#000")) < relative_luminance(parse_css_color("#fff"))
