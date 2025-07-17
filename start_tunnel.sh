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
LOG="$DIR/cloudflared.log"

if [ -n "$TOKEN" ]; then
  # use a named tunnel created in the Cloudflare dashboard
  exec cloudflared tunnel --no-autoupdate run --token "$TOKEN" --url http://localhost:$PORT >>"$LOG" 2>&1
else
  CMD=(cloudflared tunnel --url http://localhost:$PORT --no-autoupdate)
  if [ -n "$HOSTNAME" ]; then
    CMD+=(--hostname "$HOSTNAME")
  fi
  exec "${CMD[@]}" >>"$LOG" 2>&1
fi
