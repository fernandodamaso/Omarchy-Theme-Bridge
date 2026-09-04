from pathlib import Path

import pytest

from omarchy_theme_bridge_host.last_good import LastGoodStore, SnapshotError
from omarchy_theme_bridge_host.theme_loader import ThemePaths
from omarchy_theme_bridge_host.theme_normalizer import load_and_normalize

FIXTURES = Path(__file__).parent / "fixtures"


def test_last_good_round_trip_is_atomic_and_normalized(tmp_path: Path) -> None:
    store = LastGoodStore(tmp_path / "last-good-theme.json")
    theme = load_and_normalize(ThemePaths.from_theme_dir(FIXTURES / "tokyo-night"))
    store.save(theme)
    assert store.load() == theme
    assert list(tmp_path.glob("*.tmp")) == []
    assert (tmp_path / "last-good-theme.json").stat().st_mode & 0o777 == 0o600


def test_last_good_rejects_invalid_snapshot(tmp_path: Path) -> None:
    store = LastGoodStore(tmp_path / "last-good-theme.json")
    with pytest.raises(SnapshotError):
        store.save({"schemaVersion": 1, "colors": {}, "source": {}})


def test_last_good_ignores_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "last-good-theme.json"
    path.write_text("not json", encoding="utf-8")
    assert LastGoodStore(path).load() is None
