# HA-Management

A simple web based portal for managing multiple HomeAssistant systems. The application is written in Python using Flask with SQLite for storage. It offers a login system, a dashboard with a small status chart, pages to filter or inspect individual systems and a profile page to change credentials. More advanced remote management features can be added later.

## Quick start

Run the installer script on a fresh Ubuntu system to set up all dependencies, create a Python virtual environment and initialize the database. The script waits for any active apt or dpkg operations so you never need to remove lock files.  Add the `cleaninstall` argument to reinstall everything, reset the database and remove any existing WireGuard or Cloudflare configuration:

```bash
sudo bash install.sh [cleaninstall]
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

Use the **Settings** dropdown to reach pages for your profile, database backup, WireGuard and Cloudflare configuration. The **Backup** page lets you download the entire `management.db` database or upload a backup to restore from it. The Cloudflare page also allows you to start or stop the tunnel and configure the hostname, port and token.

The included Home Assistant plugin now reports the hostname, CPU and memory usage of each system. It also exposes a small API used by the portal to send remote reboot or shutdown commands.

Install the plugin on your HA system by copying the `custom_components` folder and running the included `install.sh` script. The plugin connects via WireGuard and sends heartbeats every ten minutes by default.

### Cloudflare tunnel

The portal can create a Cloudflare tunnel for secure access. The `install.sh` script installs `cloudflared` automatically. Use the Cloudflare settings page to configure the hostname, local port and optional token and to start or stop the tunnel. Running `start_tunnel.sh` manually still works if you prefer.

#### Cloudflare setup guide

1. In the [Cloudflare dashboard](https://dash.cloudflare.com/), add your domain if you have not already done so.
2. Navigate to **Zero Trust → Access → Tunnels** and create a new tunnel. Copy the generated **tunnel token**.
3. In the portal's Cloudflare page, enter your desired subdomain (e.g. `homeassistant.example.com`), the local port that the web portal listens on (default `5000`) and paste the token.
4. Click **Save** and then **Start Tunnel**. The status should change to "active" in the Cloudflare dashboard within a few seconds.
5. If you ever need to run the tunnel manually, execute `./start_tunnel.sh` from the project directory.
