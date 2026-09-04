from pathlib import Path

import pytest

from omarchy_theme_bridge_host.errors import ThemeLoadError
from omarchy_theme_bridge_host.theme_loader import ThemePaths
from omarchy_theme_bridge_host.theme_normalizer import load_and_normalize, validate_normalized_theme

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalizes_tokyo_night_semantics() -> None:
    paths = ThemePaths.from_theme_dir(FIXTURES / "tokyo-night")
    result = load_and_normalize(paths)
    assert result["name"] == "Tokyo Night"
    assert result["mode"] == "dark"
    assert result["colors"]["canvas"] == "#1a1b26"
    assert result["colors"]["surfaceRaised"] == "#24283b"
    assert result["colors"]["textStrong"] == "#c0caf5"
    assert result["colors"]["danger"] == "#f7768e"
    assert result["generation"].startswith("sha256:")
    assert validate_normalized_theme(result) is result


def test_normalizes_light_theme_and_alpha_selection() -> None:
    result = load_and_normalize(ThemePaths.from_theme_dir(FIXTURES / "light"))
    assert result["mode"] == "light"
    assert result["colors"]["canvas"] == "#fafafc"
    assert result["colors"]["selection"] == "#d2deffcc"


def test_legacy_palette_resolves_foundational_and_named_colors() -> None:
    result = load_and_normalize(ThemePaths.from_theme_dir(FIXTURES / "legacy"))
    assert result["source"]["background"] == "#101218"
    assert result["source"]["foreground"] == "#d0d4e0"
    assert result["colors"]["info"] == "#6699ee"


def test_identical_normalized_payload_has_stable_generation() -> None:
    paths = ThemePaths.from_theme_dir(FIXTURES / "tokyo-night")
    assert load_and_normalize(paths)["generation"] == load_and_normalize(paths)["generation"]


def test_invalid_toml_has_safe_error_code() -> None:
    with pytest.raises(ThemeLoadError) as error:
        load_and_normalize(ThemePaths.from_theme_dir(FIXTURES / "invalid"))
    assert error.value.code == "THEME_INVALID"
    assert "background =" not in str(error.value)


def test_mode_falls_back_to_light_marker(tmp_path: Path) -> None:
    (tmp_path / "colors.toml").write_text('background="#101010"\nforeground="#eeeeee"\n', encoding="utf-8")
    (tmp_path / "light.mode").touch()
    result = load_and_normalize(ThemePaths.from_theme_dir(tmp_path))
    assert result["mode"] == "light"
