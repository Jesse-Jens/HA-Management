# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The
application is written in Python using Flask and stores data in SQLite. It
features a basic login system and pages to list and filter clients. More
advanced features like remote reboot and WireGuard connectivity can be added
later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies,
create a Python virtual environment and initialize the database:

```bash
./install.sh
```

Afterwards activate the virtual environment and start the server:

```bash
source venv/bin/activate
python run.py
```

The default admin account uses the credentials `admin` / `admin`. Change the
password after logging in.

## Home Assistant token

Each client entry stores a Home Assistant long lived access token. Create this
token from your Home Assistant user profile and paste it into the **HA Token**
field when editing a client. It will be used for API requests sent to
`http://<client IP>:8123/api/...`.

## WireGuard connectivity

The optional download link for each client now only provides a basic WireGuard
configuration file. Use this file on the client device to establish a VPN
connection to the management server. No custom Home Assistant component is
required anymore.
