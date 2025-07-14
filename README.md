# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The application is written in Python using Flask with SQLite for storage. It offers a login system, a dashboard with a small status chart, pages to filter or inspect individual systems and a profile page to change credentials. More advanced remote management features can be added later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies, create a Python virtual environment and initialize the database. The script waits for any active apt or dpkg operations so you never need to remove lock files. Add the `cleaninstall` argument to reinstall everything and reset the database:

```bash
./install.sh [cleaninstall]
```

Afterwards activate the virtual environment and start the server:

```bash
source venv/bin/activate
python run.py
```

Log in using the default credentials `admin` / `admin` and then change the password.

Use the theme toggle in the navigation bar to switch between dark and light modes.

### Organizations and plugin

Create organizations from the "Organizations" page. Clients can be assigned to an organization and filtered by it on the clients overview.

From the dashboard or organization list you can download a small HomeAssistant plugin zip for each organization. The plugin sets up a WireGuard client and sends periodic heartbeats back to the portal so client status is shown on the dashboard.
