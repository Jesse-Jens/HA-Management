# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The
application is written in Python using Flask and stores data in SQLite. It
features a basic login system and pages to list and filter clients. More
advanced features like remote reboot and WireGuard connectivity can be added
later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies,
create a Python virtual environment and initialize the database. Add the
`cleaninstall` argument to reinstall everything and reset the database:

```bash
./install.sh [cleaninstall]
```

Afterwards activate the virtual environment and start the server:

```bash
source venv/bin/activate
python run.py
```

The default admin account uses the credentials `admin` / `admin`. Change the
password after logging in.
