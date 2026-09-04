#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

openssl genrsa -out "$tmp/dev-private.pem" 2048 >/dev/null 2>&1
openssl rsa -in "$tmp/dev-private.pem" -pubout -outform DER 2>/dev/null \
  | base64 -w0 > "$root/dev-public-key.txt"
printf '\n' >> "$root/dev-public-key.txt"
chmod 0644 "$root/dev-public-key.txt"
printf 'Wrote public development key to %s\n' "$root/dev-public-key.txt"
