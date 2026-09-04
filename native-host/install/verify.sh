#!/usr/bin/env bash
set -euo pipefail
fail() { printf 'omarchy-theme-bridge: %s\n' "$*" >&2; exit 1; }

CHROME_DIR="${HOME}/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_DIR="${HOME}/.config/chromium/NativeMessagingHosts"
while (($#)); do
  case "$1" in
    --chrome-dir) CHROME_DIR=${2:-}; shift 2 ;;
    --chromium-dir) CHROMIUM_DIR=${2:-}; shift 2 ;;
    *) fail "unknown argument: $1" ;;
  esac
done

PYTHON_BIN=${PYTHON_BIN:-python3}
python_path=$(command -v "$PYTHON_BIN") || fail "Python was not found"
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
STATE_HOME=${XDG_STATE_HOME:-"$HOME/.local/state"}
HOST_ROOT="$DATA_HOME/omarchy-theme-bridge/host"
launcher="$HOST_ROOT/omarchy-theme-bridge-host"
config="$HOST_ROOT/config.json"
ownership="$HOST_ROOT/.ownership"
hook="$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge"
manifest_name="com.omarchy.theme_bridge.json"

[[ -d $HOST_ROOT && ! -L $HOST_ROOT ]] || fail "host root is missing or unsafe"
[[ -f $ownership && ! -L $ownership ]] || fail "ownership marker is missing"
[[ $(cat "$ownership") == omarchy-theme-bridge-v1 ]] || fail "ownership marker does not match"
[[ -f $launcher && ! -L $launcher && -x $launcher ]] || fail "host launcher is missing or unsafe"
[[ -f $config && ! -L $config ]] || fail "host configuration is missing or unsafe"
[[ $(stat -c '%u' "$launcher") == $(id -u) ]] || fail "host launcher owner does not match"
[[ -z $(find "$HOST_ROOT/omarchy_theme_bridge_host" -type l -print -quit) ]] || fail "host package contains a symlink"
[[ -f $hook && ! -L $hook && -x $hook ]] || fail "Omarchy hook is missing or unsafe"
grep -q '^# omarchy-theme-bridge-owner:v1$' "$hook" || fail "Omarchy hook ownership marker does not match"

"$python_path" - "$config" "$launcher" "$CHROME_DIR/$manifest_name" "$CHROMIUM_DIR/$manifest_name" <<'PY'
import json
import os
import re
import sys
config_path, launcher, *manifests = sys.argv[1:]
with open(config_path, encoding="utf-8") as stream:
    config = json.load(stream)
if set(config) != {"allowedOrigin"} or not re.fullmatch(r"chrome-extension://[a-p]{32}/", config["allowedOrigin"]):
    raise SystemExit("invalid host config")
expected = {
    "name": "com.omarchy.theme_bridge",
    "description": "Read the active Omarchy theme for Omarchy Theme Bridge",
    "path": launcher,
    "type": "stdio",
    "allowed_origins": [config["allowedOrigin"]],
}
for path in manifests:
    if os.path.islink(path):
        raise SystemExit("unsafe manifest")
    with open(path, encoding="utf-8") as stream:
        value = json.load(stream)
    if value != expected or not os.path.isabs(value["path"]):
        raise SystemExit("manifest mismatch")
PY

PYTHONPATH="$HOST_ROOT" \
OMARCHY_THEME_BRIDGE_CONFIG="$config" \
XDG_STATE_HOME="$STATE_HOME" \
"$python_path" -m omarchy_theme_bridge_host --self-check >/dev/null
printf 'Omarchy Theme Bridge verification passed\n'
