#!/bin/bash
set -e
DIR="$(dirname "$0")"
CFG="$DIR/cloudflare.ini"
HOSTNAME=${1:-}
PORT=${PORT:-}
TOKEN=${TOKEN:-}
if [ -f "$CFG" ]; then
  CFG_HOST=$(grep -E '^hostname' "$CFG" | cut -d '=' -f2 | tr -d ' \t')
  CFG_PORT=$(grep -E '^port' "$CFG" | cut -d '=' -f2 | tr -d ' \t')
  CFG_TOKEN=$(grep -E '^token' "$CFG" | cut -d '=' -f2 | tr -d ' \t')
  HOSTNAME=${HOSTNAME:-$CFG_HOST}
  PORT=${PORT:-$CFG_PORT}
  TOKEN=${TOKEN:-$CFG_TOKEN}
fi
HOSTNAME=${HOSTNAME:-homeassistant.jayjaysrv.com}
PORT=${PORT:-5000}
if ! command -v cloudflared >/dev/null; then
  echo "cloudflared not installed. Run install.sh first." >&2
  exit 1
fi
CMD=(cloudflared tunnel --url http://localhost:$PORT --no-autoupdate)
if [ -n "$HOSTNAME" ]; then
  CMD+=(--hostname "$HOSTNAME")
fi
if [ -n "$TOKEN" ]; then
  CMD+=(--token "$TOKEN")
fi
"${CMD[@]}"
