from __future__ import annotations

import json
import os
import select
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import BinaryIO

import pytest

from omarchy_theme_bridge_host.protocol import read_message, write_message

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux inotify required")
EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"
ORIGIN = f"chrome-extension://{EXTENSION_ID}/"


def write_theme(directory: Path, *, background: str, accent: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "colors.toml").write_text(
        "\n".join([
            'mode = "dark"',
            f'background = "{background}"',
            'foreground = "#c0caf5"',
            f'accent = "{accent}"',
            'red = "#f7768e"',
            'green = "#9ece6a"',
            'yellow = "#e0af68"',
            'blue = "#7aa2f7"',
            'magenta = "#bb9af7"',
            'cyan = "#7dcfff"',
            "",
        ]),
        encoding="utf-8",
    )
    (directory / "theme.name").write_text("Test Theme\n", encoding="utf-8")


def receive(stream: BinaryIO, timeout: float = 3.0) -> dict[str, object]:
    ready, _, _ = select.select([stream], [], [], timeout)
    assert ready, "timed out waiting for native message"
    message = read_message(stream)
    assert message is not None
    return message


def test_native_host_handshake_change_and_last_good_error(tmp_path: Path) -> None:
    theme = tmp_path / "theme"
    write_theme(theme, background="#1a1b26", accent="#7aa2f7")
    state = tmp_path / "state"
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")

    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(Path(__file__).parents[1]),
        "OMARCHY_THEME_BRIDGE_CONFIG": str(config),
        "OMARCHY_THEME_BRIDGE_THEME_DIR": str(theme),
        "XDG_STATE_HOME": str(state),
    })
    process = subprocess.Popen(
        [sys.executable, "-m", "omarchy_theme_bridge_host", ORIGIN],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdin is not None
    assert process.stdout is not None

    write_message(process.stdin, {
        "type": "hello",
        "protocolVersion": 1,
        "extensionVersion": "0.1.0",
    })
    assert receive(process.stdout)["type"] == "host.ready"
    snapshot = receive(process.stdout)
    assert snapshot["type"] == "theme.snapshot"
    first_generation = snapshot["theme"]["generation"]  # type: ignore[index]

    replacement = tmp_path / "next-theme"
    write_theme(replacement, background="#202230", accent="#bb9af7")
    old = tmp_path / "old-theme"
    theme.rename(old)
    replacement.rename(theme)

    changed = receive(process.stdout)
    assert changed["type"] == "theme.changed"
    second_generation = changed["theme"]["generation"]  # type: ignore[index]
    assert second_generation != first_generation

    (theme / "colors.toml").write_text("background = [\n", encoding="utf-8")
    error = receive(process.stdout)
    assert error == {
        "type": "theme.error",
        "code": "THEME_INVALID",
        "retainedGeneration": second_generation,
    }

    process.stdin.close()
    assert process.wait(timeout=3) == 0
    stderr = process.stderr.read().decode() if process.stderr else ""
    assert "background =" not in stderr
    assert str(theme) not in stderr


def test_native_host_exits_on_oversized_frame_header(tmp_path: Path) -> None:
    theme = tmp_path / "theme"
    write_theme(theme, background="#1a1b26", accent="#7aa2f7")
    state = tmp_path / "state"
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")

    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(Path(__file__).parents[1]),
        "OMARCHY_THEME_BRIDGE_CONFIG": str(config),
        "OMARCHY_THEME_BRIDGE_THEME_DIR": str(theme),
        "XDG_STATE_HOME": str(state),
    })
    process = subprocess.Popen(
        [sys.executable, "-m", "omarchy_theme_bridge_host", ORIGIN],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdin is not None
    assert process.stdout is not None

    try:
        process.stdin.write(struct.pack("=I", 65_537))
        process.stdin.flush()
        assert process.wait(timeout=1.0) == 5
        assert receive(process.stdout) == {
            "type": "theme.error",
            "code": "PROTOCOL_MISMATCH",
        }
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)
