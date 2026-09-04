#!/usr/bin/env bash
set -euo pipefail
fail() { printf 'omarchy-theme-bridge: %s\n' "$*" >&2; exit 1; }
[[ $(id -u) -ne 0 ]] || fail "must not run as root"

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
ownership="$HOST_ROOT/.ownership"
hook="$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge"
manifest_name="com.omarchy.theme_bridge.json"

if [[ -e $HOST_ROOT ]]; then
  [[ -d $HOST_ROOT && ! -L $HOST_ROOT ]] || fail "host root is unsafe"
  [[ -f $ownership && ! -L $ownership ]] || fail "ownership marker is missing"
  [[ $(cat "$ownership") == omarchy-theme-bridge-v1 ]] || fail "ownership marker does not match"
fi

validate_manifest() {
  local manifest=$1
  [[ -e $manifest ]] || return 0
  [[ -f $manifest && ! -L $manifest ]] || fail "manifest is unsafe: $manifest"
  "$python_path" - "$manifest" "$launcher" <<'PY'
import json
import re
import sys
path, launcher = sys.argv[1:]
with open(path, encoding="utf-8") as stream:
    value = json.load(stream)
if set(value) != {"name", "description", "path", "type", "allowed_origins"}:
    raise SystemExit(1)
if value["name"] != "com.omarchy.theme_bridge" or value["path"] != launcher or value["type"] != "stdio":
    raise SystemExit(1)
origins = value["allowed_origins"]
if not isinstance(origins, list) or len(origins) != 1 or not re.fullmatch(r"chrome-extension://[a-p]{32}/", origins[0]):
    raise SystemExit(1)
PY
}

for manifest in "$CHROME_DIR/$manifest_name" "$CHROMIUM_DIR/$manifest_name"; do
  validate_manifest "$manifest" || fail "manifest ownership does not match: $manifest"
done
if [[ -e $hook ]]; then
  [[ -f $hook && ! -L $hook ]] || fail "hook is unsafe"
  grep -q '^# omarchy-theme-bridge-owner:v1$' "$hook" || fail "hook ownership marker does not match"
fi

for manifest in "$CHROME_DIR/$manifest_name" "$CHROMIUM_DIR/$manifest_name"; do
  if [[ -e $manifest ]]; then rm -- "$manifest"; printf '%s\n' "$manifest"; fi
done
if [[ -e $hook ]]; then rm -- "$hook"; printf '%s\n' "$hook"; fi
if [[ -e $HOST_ROOT ]]; then rm -rf -- "$HOST_ROOT"; printf '%s\n' "$HOST_ROOT"; fi
state_dir="$STATE_HOME/omarchy-theme-bridge"
if [[ -d $state_dir && ! -L $state_dir ]]; then
  find "$state_dir" -maxdepth 1 -type f \( -name 'theme-set.signal' -o -name 'last-good-theme.json' \) -delete
  rmdir "$state_dir" 2>/dev/null || true
fi
