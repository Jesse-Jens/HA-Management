#!/bin/bash
set -e

if ! command -v wg >/dev/null; then
    apt-get update
    apt-get install -y wireguard
fi

cp client.conf /etc/wireguard/wg0.conf
wg-quick up wg0

python3 client.py &>/var/log/ha_plugin.log &
