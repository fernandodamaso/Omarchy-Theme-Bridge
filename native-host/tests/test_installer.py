from __future__ import annotations

import json
import os
import pwd
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "install" / "install.sh"
VERIFY = ROOT / "install" / "verify.sh"
UNINSTALL = ROOT / "install" / "uninstall.sh"
EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


def prepare_environment(tmp_path: Path) -> tuple[dict[str, str], list[str]]:
    home = tmp_path / "home"
    data = tmp_path / "data"
    state = tmp_path / "state"
    chrome = tmp_path / "chrome-hosts"
    chromium = tmp_path / "chromium-hosts"
    for path in (home, data, state, chrome, chromium):
        path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "XDG_DATA_HOME": str(data),
        "XDG_STATE_HOME": str(state),
        "PYTHON_BIN": shutil.which("python3") or "python3",
    })
    prefix: list[str] = []
    if os.geteuid() == 0:
        for parent in (tmp_path.parent, tmp_path.parent.parent):
            parent.chmod(0o755)
        nobody = pwd.getpwnam("nobody")
        for path in (tmp_path, home, data, state, chrome, chromium):
            os.chown(path, nobody.pw_uid, nobody.pw_gid)
            path.chmod(0o755)
        prefix = ["runuser", "-u", "nobody", "--", "env", *[f"{key}={value}" for key, value in env.items()]]
        env = os.environ.copy()
    args = ["--chrome-dir", str(chrome), "--chromium-dir", str(chromium)]
    return env, prefix + args


def command(script: Path, env: dict[str, str], prefixed_args: list[str], *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    if prefixed_args and prefixed_args[0] == "runuser":
        separator = prefixed_args.index("--")
        env_prefix = prefixed_args[:separator + 2]
        browser_args_index = next(index for index, value in enumerate(prefixed_args) if value == "--chrome-dir")
        env_items = prefixed_args[separator + 2:browser_args_index]
        browser_args = prefixed_args[browser_args_index:]
        argv = [*env_prefix, *env_items, "bash", str(script), *args, *browser_args]
        return subprocess.run(argv, text=True, capture_output=True, check=check)
    return subprocess.run(["bash", str(script), *args, *prefixed_args], env=env, text=True, capture_output=True, check=check)


def test_install_is_idempotent_and_pins_both_browser_manifests(tmp_path: Path) -> None:
    env, args = prepare_environment(tmp_path)
    command(INSTALL, env, args, "--extension-id", EXTENSION_ID)
    command(INSTALL, env, args, "--extension-id", EXTENSION_ID)

    chrome = json.loads((tmp_path / "chrome-hosts/com.omarchy.theme_bridge.json").read_text())
    chromium = json.loads((tmp_path / "chromium-hosts/com.omarchy.theme_bridge.json").read_text())
    assert chrome == chromium
    assert chrome["name"] == "com.omarchy.theme_bridge"
    assert chrome["type"] == "stdio"
    assert chrome["allowed_origins"] == [f"chrome-extension://{EXTENSION_ID}/"]
    assert Path(chrome["path"]).is_absolute()
    assert Path(chrome["path"]).is_file()

    result = command(VERIFY, env, args)
    assert "verification passed" in result.stdout


def test_uninstall_keeps_unrelated_hook_and_parent_directories(tmp_path: Path) -> None:
    env, args = prepare_environment(tmp_path)
    unrelated = tmp_path / "home/.config/omarchy/hooks/unrelated"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("keep", encoding="utf-8")
    if os.geteuid() == 0:
        nobody = pwd.getpwnam("nobody")
        os.chown(unrelated.parent, nobody.pw_uid, nobody.pw_gid)
        os.chown(unrelated, nobody.pw_uid, nobody.pw_gid)

    command(INSTALL, env, args, "--extension-id", EXTENSION_ID)
    command(UNINSTALL, env, args)

    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert unrelated.parent.is_dir()
    assert not (tmp_path / "data/omarchy-theme-bridge/host").exists()
    assert not (tmp_path / "chrome-hosts/com.omarchy.theme_bridge.json").exists()


def test_invalid_extension_id_fails_without_writes(tmp_path: Path) -> None:
    env, args = prepare_environment(tmp_path)
    result = command(INSTALL, env, args, "--extension-id", "not-an-id", check=False)
    assert result.returncode != 0
    assert not (tmp_path / "data/omarchy-theme-bridge").exists()


def test_uninstall_refuses_ownership_marker_mismatch(tmp_path: Path) -> None:
    env, args = prepare_environment(tmp_path)
    command(INSTALL, env, args, "--extension-id", EXTENSION_ID)
    marker = tmp_path / "data/omarchy-theme-bridge/host/.ownership"
    marker.write_text("someone-else\n", encoding="utf-8")
    if os.geteuid() == 0:
        nobody = pwd.getpwnam("nobody")
        os.chown(marker, nobody.pw_uid, nobody.pw_gid)
    result = command(UNINSTALL, env, args, check=False)
    assert result.returncode != 0
    assert marker.exists()


def test_install_refuses_symlinked_browser_directory(tmp_path: Path) -> None:
    env, args = prepare_environment(tmp_path)
    chrome_dir = tmp_path / "chrome-hosts"
    chrome_dir.rmdir()
    chrome_dir.symlink_to(tmp_path / "state", target_is_directory=True)
    result = command(INSTALL, env, args, "--extension-id", EXTENSION_ID, check=False)
    assert result.returncode != 0


def test_installer_rejects_root_execution(tmp_path: Path) -> None:
    if os.geteuid() != 0:
        pytest.skip("requires root test runner")
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        ["bash", str(INSTALL), "--extension-id", EXTENSION_ID],
        env={**os.environ, "HOME": str(home)},
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "must not run as root" in result.stderr
