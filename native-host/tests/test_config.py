import json
from pathlib import Path

import pytest

from omarchy_theme_bridge_host.config import CallerForbidden, ConfigError, HostConfig


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"
ORIGIN = f"chrome-extension://{EXTENSION_ID}/"


def test_config_accepts_exact_installed_origin(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")
    HostConfig.load(path).assert_caller(["host", ORIGIN])


def test_config_rejects_other_extension(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")
    with pytest.raises(CallerForbidden):
        HostConfig.load(path).assert_caller([
            "host",
            "chrome-extension://pppppppppppppppppppppppppppppppp/",
        ])


def test_config_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError):
        HostConfig.load(path)


def test_config_rejects_extra_fields(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowedOrigin": ORIGIN, "url": "https://example.com"}), encoding="utf-8")
    with pytest.raises(ConfigError):
        HostConfig.load(path)
