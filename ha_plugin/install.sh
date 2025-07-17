#!/bin/bash
set -e

if ! command -v wg >/dev/null; then
    apt-get update
    apt-get install -y wireguard
fi

mkdir -p /etc/wireguard
cp client.conf /etc/wireguard/wg0.conf
wg-quick up wg0

cp -r custom_components/ha_management "$HOME/.homeassistant/custom_components/"
cp config.ini /etc/ha_plugin.conf
pip3 install requests flask psutil

nohup python3 custom_components/ha_management/heartbeat.py &>/var/log/ha_plugin.log &
