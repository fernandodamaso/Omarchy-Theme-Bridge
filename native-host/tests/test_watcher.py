import sys
from pathlib import Path

import pytest

from omarchy_theme_bridge_host.theme_loader import ThemePaths
from omarchy_theme_bridge_host.watcher import InotifyWatcher

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux inotify required")


def write_theme(directory: Path, background: str = "#000000", foreground: str = "#ffffff") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "colors.toml").write_text(
        f'background="{background}"\nforeground="{foreground}"\n',
        encoding="utf-8",
    )


def test_detects_atomic_active_theme_directory_replacement(tmp_path: Path) -> None:
    current = tmp_path / "current"
    theme = current / "theme"
    write_theme(theme)
    paths = ThemePaths(
        theme_dir=theme,
        colors_file=theme / "colors.toml",
        name_file=current / "theme.name",
        light_marker=theme / "light.mode",
    )
    signal = tmp_path / "state" / "theme-set.signal"
    signal.parent.mkdir()
    watcher = InotifyWatcher(paths, signal)

    replacement = current / "next-theme"
    write_theme(replacement, "#111111", "#eeeeee")
    old = current / "old-theme"
    theme.rename(old)
    replacement.rename(theme)

    events = watcher.wait_for_events(timeout=1.0)
    assert events.reload_requested is True
    assert events.rearm_requested is True
    watcher.close()


def test_detects_atomic_hook_signal(tmp_path: Path) -> None:
    current = tmp_path / "current"
    theme = current / "theme"
    write_theme(theme)
    signal = tmp_path / "state" / "theme-set.signal"
    signal.parent.mkdir()
    watcher = InotifyWatcher(
        ThemePaths(theme, theme / "colors.toml", current / "theme.name", theme / "light.mode"),
        signal,
    )
    temporary = signal.parent / ".signal.tmp"
    temporary.write_text("changed\n", encoding="utf-8")
    temporary.replace(signal)
    assert watcher.wait_for_events(timeout=1.0).reload_requested is True
    watcher.close()


def test_rearm_has_no_synthetic_events_and_tracks_new_theme(tmp_path: Path) -> None:
    current = tmp_path / "current"
    theme = current / "theme"
    write_theme(theme)
    signal = tmp_path / "state" / "theme-set.signal"
    signal.parent.mkdir()
    paths = ThemePaths(theme, theme / "colors.toml", current / "theme.name", theme / "light.mode")
    watcher = InotifyWatcher(paths, signal)

    replacement = current / "next-theme"
    write_theme(replacement, "#111111", "#eeeeee")
    theme.rename(current / "old-theme")
    replacement.rename(theme)

    batch = watcher.wait_for_events(timeout=1.0)
    assert batch.rearm_requested is True
    watcher.rearm()

    synthetic = watcher.wait_for_events(timeout=0.05)
    assert synthetic.reload_requested is False
    assert synthetic.rearm_requested is False

    (theme / "colors.toml").write_text(
        'background="#222222"\nforeground="#dddddd"\n',
        encoding="utf-8",
    )
    changed = watcher.wait_for_events(timeout=1.0)
    assert changed.reload_requested is True
    watcher.close()
