# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The application is written in Python using Flask with SQLite for storage. It offers a basic login system, a dashboard to view all clients and pages to filter or inspect individual systems. More advanced remote management features can be added later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies, create a Python virtual environment and initialize the database. Add the `cleaninstall` argument to reinstall everything and reset the database:

```bash
./install.sh [cleaninstall]
```

Afterwards activate the virtual environment and start the server:

```bash
source venv/bin/activate
python run.py
```

Log in using the default credentials `admin` / `admin` and then change the password.
