#!/usr/bin/env bash
# omarchy-theme-bridge-owner:v1
set -euo pipefail
state_home=${XDG_STATE_HOME:-"$HOME/.local/state"}
dir="$state_home/omarchy-theme-bridge"
mkdir -p "$dir"
tmp=$(mktemp "$dir/.theme-set.signal.XXXXXX")
printf '%s\n' changed > "$tmp"
chmod 0600 "$tmp"
mv -f "$tmp" "$dir/theme-set.signal"
