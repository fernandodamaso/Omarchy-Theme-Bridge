from __future__ import annotations

import os
import sys
from pathlib import Path

from .config import CallerForbidden, ConfigError, HostConfig
from .host import NativeHost
from .theme_loader import ThemePaths
from .watcher import InotifyWatcher


def _config_path() -> Path:
    package_root = Path(__file__).resolve().parent.parent
    return Path(os.environ.get("OMARCHY_THEME_BRIDGE_CONFIG", package_root / "config.json"))


def _self_check(config: HostConfig) -> int:
    home = Path.home()
    paths = ThemePaths.resolve(home, os.environ.get("OMARCHY_THEME_BRIDGE_THEME_DIR"))
    state_home = Path(os.environ.get("XDG_STATE_HOME", str(home / ".local" / "state")))
    state_dir = state_home / "omarchy-theme-bridge"
    state_dir.mkdir(parents=True, exist_ok=True)
    watcher = InotifyWatcher(paths, state_dir / "theme-set.signal")
    watcher.close()
    print("omarchy-theme-bridge-host: self-check ok", file=sys.stderr)
    return 0


def main() -> int:
    try:
        config = HostConfig.load(_config_path())
        if "--self-check" in sys.argv[1:]:
            return _self_check(config)
        config.assert_caller(sys.argv)
        host = NativeHost.from_environment(config=config, home=Path.home(), environ=os.environ)
        return host.run(sys.stdin.buffer, sys.stdout.buffer)
    except CallerForbidden:
        print("omarchy-theme-bridge-host: CALLER_FORBIDDEN", file=sys.stderr)
        return 3
    except ConfigError:
        print("omarchy-theme-bridge-host: CONFIG_INVALID", file=sys.stderr)
        return 2
    except OSError:
        print("omarchy-theme-bridge-host: HOST_START_FAILED", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
