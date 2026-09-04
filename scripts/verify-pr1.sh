#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)

cd "$root/extension"
npm ci --ignore-scripts
npm run typecheck
npm test
npm run build
node -e 'const m=require("./dist/manifest.json"); if(m.manifest_version!==3) process.exit(1)'
for file in \
  dist/background/service-worker.js \
  dist/content/content-script.js \
  dist/popup/index.html \
  dist/options/index.html \
  dist/manifest.json; do
  [[ -f $file ]] || { printf 'missing build artifact: %s\n' "$file" >&2; exit 1; }
done

cd "$root/native-host"
python_bin=${PYTHON_BIN:-python3}
"$python_bin" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
"$python_bin" -m compileall -q omarchy_theme_bridge_host
"$python_bin" -m pytest -q

printf 'PR 1 verification passed\n'
