#!/usr/bin/env bash
set -euo pipefail

fail() { printf 'omarchy-theme-bridge: %s\n' "$*" >&2; exit 1; }
[[ $(id -u) -ne 0 ]] || fail "must not run as root"
[[ $(uname -s) == Linux ]] || fail "Linux is required"

EXTENSION_ID=""
CHROME_DIR="${HOME}/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_DIR="${HOME}/.config/chromium/NativeMessagingHosts"
while (($#)); do
  case "$1" in
    --extension-id) EXTENSION_ID=${2:-}; shift 2 ;;
    --chrome-dir) CHROME_DIR=${2:-}; shift 2 ;;
    --chromium-dir) CHROMIUM_DIR=${2:-}; shift 2 ;;
    -h|--help)
      printf 'Usage: %s --extension-id <32-character-a-through-p-id> [--chrome-dir <dir>] [--chromium-dir <dir>]\n' "$0"
      exit 0
      ;;
    *) fail "unknown argument: $1" ;;
  esac
done
[[ $EXTENSION_ID =~ ^[a-p]{32}$ ]] || fail "invalid extension ID"

PYTHON_BIN=${PYTHON_BIN:-python3}
python_path=$(command -v "$PYTHON_BIN") || fail "Python 3.11+ was not found"
python_path=$(readlink -f "$python_path")
"$python_path" - <<'PY' || fail "Python 3.11+ is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
source_package="$repo_root/native-host/omarchy_theme_bridge_host"
source_hook="$script_dir/theme-set-hook.sh"
[[ -d $source_package && ! -L $source_package ]] || fail "native host package is unavailable"
[[ -f $source_hook && ! -L $source_hook ]] || fail "theme hook template is unavailable"

DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
STATE_HOME=${XDG_STATE_HOME:-"$HOME/.local/state"}
project_root="$DATA_HOME/omarchy-theme-bridge"
HOST_ROOT="$project_root/host"
launcher="$HOST_ROOT/omarchy-theme-bridge-host"
config="$HOST_ROOT/config.json"
ownership="$HOST_ROOT/.ownership"
hook_dir="$HOME/.config/omarchy/hooks"
hook="$hook_dir/theme-set-omarchy-theme-bridge"
manifest_name="com.omarchy.theme_bridge.json"
origin="chrome-extension://$EXTENSION_ID/"

for directory in "$project_root" "$CHROME_DIR" "$CHROMIUM_DIR" "$hook_dir"; do
  [[ ! -L $directory ]] || fail "refusing symlinked directory: $directory"
  mkdir -p "$directory"
done
[[ ! -L $HOST_ROOT ]] || fail "refusing symlinked host root"
if [[ -e $HOST_ROOT ]]; then
  [[ -f $ownership && ! -L $ownership ]] || fail "existing host root is not project-owned"
  [[ $(cat "$ownership") == omarchy-theme-bridge-v1 ]] || fail "existing host ownership marker does not match"
fi
for target in "$CHROME_DIR/$manifest_name" "$CHROMIUM_DIR/$manifest_name" "$hook"; do
  [[ ! -L $target ]] || fail "refusing symlinked target: $target"
done

stage=$(mktemp -d "$project_root/.host-stage.XXXXXX")
backup=""
cleanup() {
  rm -rf -- "$stage"
  [[ -z $backup || ! -e $backup ]] || rm -rf -- "$backup"
}
trap cleanup EXIT

cp -a "$source_package" "$stage/omarchy_theme_bridge_host"
printf '%s\n' omarchy-theme-bridge-v1 > "$stage/.ownership"
chmod 0644 "$stage/.ownership"

"$python_path" - "$stage/config.json" "$origin" <<'PY'
import json
import os
import sys
path, origin = sys.argv[1:]
tmp = f"{path}.tmp"
with open(tmp, "w", encoding="utf-8") as stream:
    json.dump({"allowedOrigin": origin}, stream, separators=(",", ":"))
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(tmp, 0o600)
os.replace(tmp, path)
PY

cat > "$stage/omarchy-theme-bridge-host" <<EOF2
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$HOST_ROOT"
export OMARCHY_THEME_BRIDGE_CONFIG="$HOST_ROOT/config.json"
exec "$python_path" -m omarchy_theme_bridge_host "\$@"
EOF2
chmod 0755 "$stage/omarchy-theme-bridge-host"

PYTHONPATH="$stage" \
OMARCHY_THEME_BRIDGE_CONFIG="$stage/config.json" \
XDG_STATE_HOME="$STATE_HOME" \
"$python_path" -m omarchy_theme_bridge_host --self-check >/dev/null

if [[ -e $HOST_ROOT ]]; then
  backup="$project_root/.host-backup.$$"
  mv "$HOST_ROOT" "$backup"
fi
mv "$stage" "$HOST_ROOT"
stage="$project_root/.stage-consumed"
[[ -z $backup ]] || rm -rf -- "$backup"
backup=""

write_manifest() {
  local directory=$1 target tmp
  target="$directory/$manifest_name"
  tmp=$(mktemp "$directory/.${manifest_name}.XXXXXX")
  "$python_path" - "$tmp" "$launcher" "$origin" <<'PY'
import json
import os
import sys
path, launcher, origin = sys.argv[1:]
value = {
    "name": "com.omarchy.theme_bridge",
    "description": "Read the active Omarchy theme for Omarchy Theme Bridge",
    "path": launcher,
    "type": "stdio",
    "allowed_origins": [origin],
}
with open(path, "w", encoding="utf-8") as stream:
    json.dump(value, stream, indent=2)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(path, 0o644)
PY
  mv -f "$tmp" "$target"
  printf '%s\n' "$target"
}

write_manifest "$CHROME_DIR"
write_manifest "$CHROMIUM_DIR"
hook_tmp=$(mktemp "$hook_dir/.theme-set-omarchy-theme-bridge.XXXXXX")
cp "$source_hook" "$hook_tmp"
chmod 0755 "$hook_tmp"
mv -f "$hook_tmp" "$hook"
printf '%s\n' "$HOST_ROOT" "$hook"
