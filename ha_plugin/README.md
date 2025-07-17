This Home Assistant custom component connects your instance to the management portal using WireGuard and periodic heartbeats.

1. Copy the `custom_components/ha_management` folder into your Home Assistant `config/custom_components` directory.
2. Edit `config.ini` with the organization and client identifiers plus VPN details if needed.
3. Run `./install.sh` on the Home Assistant host to install Python requirements, set up WireGuard and start the heartbeat service.

The heartbeat service also exposes an HTTP API on port 5001 that accepts `reboot`, `shutdown`, `update` and `shell` commands. This allows the management portal to perform remote updates and execute shell commands when needed.
