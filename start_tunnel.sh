#!/bin/bash
set -e
HOSTNAME=${1:-homeassistant.jayjaysrv.com}
PORT=${PORT:-5000}
if ! command -v cloudflared >/dev/null; then
  echo "cloudflared not installed. Run install.sh first." >&2
  exit 1
fi
cloudflared tunnel --url http://localhost:$PORT --no-autoupdate --hostname $HOSTNAME
