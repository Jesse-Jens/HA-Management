#!/bin/bash
set -e
DIR="$(dirname "$0")"
CFG="$DIR/cloudflare.ini"
LABEL=${1:-interface}

get_cfg() {
  python3 - "$CFG" "$LABEL" "$1" <<'EOF'
import configparser,sys
cfg=configparser.ConfigParser(); cfg.read(sys.argv[1])
print(cfg.get(sys.argv[2], sys.argv[3], fallback=""))
EOF
}

HOSTNAME=${HOSTNAME:-$(get_cfg hostname)}
PORT=${PORT:-$(get_cfg port)}
TOKEN=${TOKEN:-$(get_cfg token)}

if [ -z "$HOSTNAME" ]; then
  if [ "$LABEL" = "vpn" ]; then
    HOSTNAME="vpn-ha-management.jayjaysrv.com"
  else
    HOSTNAME="ha-management.jayjaysrv.com"
  fi
fi
PORT=${PORT:-5000}
if ! command -v cloudflared >/dev/null; then
  echo "cloudflared not installed. Run install.sh first." >&2
  exit 1
fi
LOG="$DIR/cloudflared_${LABEL}.log"

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
