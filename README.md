# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The application is written in Python using Flask with SQLite for storage. It offers a login system, a dashboard with a small status chart, pages to filter or inspect individual systems and a profile page to change credentials. More advanced remote management features can be added later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies, create a Python virtual environment and initialize the database. The script waits for any active apt or dpkg operations so you never need to remove lock files. You can execute the script from any directory as it now changes to its own location. Add the `cleaninstall` argument to reinstall everything, reset the database and remove any existing WireGuard configuration:

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

The installer also sets up a basic WireGuard server configuration at `/etc/wireguard/wg0.conf`. Visit the "WireGuard" page after logging in to edit this configuration directly from the portal.

The dashboard shows a small system monitor so you can keep an eye on CPU and memory usage of the server running the portal.

### Organizations and plugin

Create organizations from the "Organizations" page. Clients can be assigned to an organization and filtered by it on the clients overview.

Add clients under an organization and download a plugin per client. Each client gets its own WireGuard key pair and IP address. Downloading the plugin again reuses the stored keys so no duplicate peers are added to `wg0.conf`.

Use the **Backup** page in the navigation bar to download the entire `management.db` database or upload a backup to restore from it.

The included Home Assistant plugin now reports the hostname, CPU and memory usage of each system. It also exposes a small API used by the portal to send remote reboot or shutdown commands.

Install the plugin on your HA system by copying the `custom_components` folder and running the included `install.sh` script. The plugin connects via WireGuard and sends heartbeats every ten minutes by default.

### Cloudflare tunnel

To expose the portal securely on the public internet you can use Cloudflare's tunnel service. The
`install.sh` script installs `cloudflared` automatically. Start the server and then run:

```bash
./start_tunnel.sh
```

This creates a tunnel to `homeassistant.jayjaysrv.com` forwarding to
`http://localhost:$PORT` (default 5000). You can override the subdomain by
passing it as the first argument or change the port using the `PORT` environment
variable.
