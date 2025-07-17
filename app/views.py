import os
import secrets
import configparser
import subprocess
import psutil
import signal
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_user, login_required, logout_user, current_user
from .models import Client, User, Organization
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

main_bp = Blueprint('main', __name__)


def _append_peer(public_key, allowed_ip):
    wg_conf = current_app.config.get('WG_CONFIG', '/etc/wireguard/wg0.conf')
    peer_block = f"\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {allowed_ip}\n"
    try:
        existing = ''
        if os.path.exists(wg_conf):
            with open(wg_conf) as f:
                existing = f.read()
        if allowed_ip not in existing:
            with open(wg_conf, 'a') as f:
                f.write(peer_block)
            subprocess.run(['sudo', 'systemctl', 'restart', 'wg-quick@wg0'], check=False)
    except Exception:
        pass

def _remove_peer(public_key):
    wg_conf = current_app.config.get('WG_CONFIG', '/etc/wireguard/wg0.conf')
    try:
        iface, peers = _parse_wg_config(wg_conf)
        new_peers = [p for p in peers if p.get('PublicKey') != public_key]
        if len(new_peers) != len(peers):
            with open(wg_conf, 'w') as f:
                f.write('[Interface]\n')
                for k, v in iface.items():
                    f.write(f'{k} = {v}\n')
                for p in new_peers:
                    f.write('\n[Peer]\n')
                    for k, v in p.items():
                        f.write(f'{k} = {v}\n')
            subprocess.run(['sudo', 'systemctl', 'restart', 'wg-quick@wg0'], check=False)
    except Exception:
        pass

def _parse_wg_config(path):
    interface = {}
    peers = []
    current = None
    if not os.path.exists(path):
        return interface, peers
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line == '[Interface]':
                current = interface
            elif line == '[Peer]':
                current = {}
                peers.append(current)
            elif '=' in line and current is not None:
                k, v = line.split('=', 1)
                current[k.strip()] = v.strip()
    return interface, peers


def _tunnel_pid_file(label):
    return os.path.join(current_app.config['BASEDIR'], f'cloudflared_{label}.pid')


def _tunnel_running(label):
    pid_file = _tunnel_pid_file(label)
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except Exception:
            os.remove(pid_file)
    return False


def _start_tunnel(label):
    if _tunnel_running(label):
        return
    script = os.path.join(current_app.config['BASEDIR'], 'start_tunnel.sh')
    p = subprocess.Popen(['bash', script, label])
    with open(_tunnel_pid_file(label), 'w') as f:
        f.write(str(p.pid))


def _stop_tunnel(label):
    pid_file = _tunnel_pid_file(label)
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        os.remove(pid_file)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login', next=url_for('main.dashboard')))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    clients = Client.query.all()
    orgs = Organization.query.all()
    counts = {
        'healthy': Client.query.filter_by(status='online').count(),
        'attention': Client.query.filter_by(status='warning').count(),
        'critical': Client.query.filter_by(status='critical').count(),
        'offline': Client.query.filter_by(status='offline').count(),
    }
    sys_stats = {
        'cpu': psutil.cpu_percent(interval=None),
        'memory': psutil.virtual_memory().percent,
    }
    return render_template('dashboard.html', clients=clients, orgs=orgs, counts=counts, sys_stats=sys_stats)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_page)
        flash('Invalid username or password')
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main_bp.route('/clients')
@login_required
def clients_list():
    q = request.args.get('q', '')
    org_id = request.args.get('org')
    query = Client.query
    if org_id:
        query = query.filter_by(organization_id=org_id)
    if q:
        query = query.filter(Client.name.contains(q))
    clients = query.all()
    orgs = Organization.query.all()
    return render_template('clients.html', clients=clients, q=q, orgs=orgs, org_id=org_id)

@main_bp.route('/clients/export')
@login_required
def export_clients():
    import json
    data = []
    for org in Organization.query.all():
        org_data = {
            'id': org.id,
            'name': org.name,
            'api_key': org.api_key,
            'clients': []
        }
        for c in org.clients:
            org_data['clients'].append({
                'id': c.id,
                'name': c.name,
                'location': c.location,
                'status': c.status,
                'ip_address': c.ip_address
            })
        data.append(org_data)
    resp = current_app.response_class(
        json.dumps(data, indent=2),
        mimetype='application/json'
    )
    resp.headers['Content-Disposition'] = 'attachment; filename=clients.json'
    return resp

@main_bp.route('/backup', methods=['GET', 'POST'])
@login_required
def backup():
    db_path = current_app.config['DB_PATH']
    if request.method == 'POST':
        file = request.files.get('db')
        if file:
            file.save(db_path)
            flash('Database imported')
            return redirect(url_for('main.backup'))
    if request.args.get('download'):
        return send_file(db_path, as_attachment=True)
    return render_template('backup.html')

@main_bp.route('/client/add', methods=['GET', 'POST'])
@login_required
def client_add():
    orgs = Organization.query.all()
    if request.method == 'POST':
        name = request.form['name']
        org_id = request.form.get('organization_id')
        client = Client(name=name, organization_id=org_id)
        db.session.add(client)
        db.session.commit()
        flash('Client added')
        return redirect(url_for('main.clients_list'))
    return render_template('client_add.html', orgs=orgs)

@main_bp.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def client_edit(client_id):
    client = Client.query.get_or_404(client_id)
    orgs = Organization.query.all()
    if request.method == 'POST':
        client.name = request.form['name']
        client.location = request.form.get('location')
        client.organization_id = request.form.get('organization_id')
        db.session.commit()
        flash('Client updated')
        return redirect(url_for('main.clients_list'))
    return render_template('client_edit.html', client=client, orgs=orgs)

@main_bp.route('/client/<int:client_id>/delete')
@login_required
def client_delete(client_id):
    client = Client.query.get_or_404(client_id)
    if client.wg_public_key:
        _remove_peer(client.wg_public_key)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted')
    return redirect(url_for('main.clients_list'))

@main_bp.route('/client/<int:client_id>/action/<cmd>')
@login_required
def client_action(client_id, cmd):
    import requests
    client = Client.query.get_or_404(client_id)
    ip = client.ip_address.split('/')[0]
    url = f'http://{ip}:5001/action'
    try:
        requests.post(url, json={'cmd': cmd, 'api_key': client.organization.api_key}, timeout=5)
        flash(f'{cmd.capitalize()} command sent')
    except Exception as exc:
        flash(f'Failed: {exc}')
    return redirect(url_for('main.client_manage', client_id=client_id))

@main_bp.route('/client/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('client.html', client=client)

@main_bp.route('/client/<int:client_id>/manage', methods=['GET', 'POST'])
@login_required
def client_manage(client_id):
    client = Client.query.get_or_404(client_id)
    output = None
    if request.method == 'POST':
        cmd = request.form.get('cmd')
        if cmd:
            import requests
            ip = client.ip_address.split('/')[0]
            url = f'http://{ip}:5001/shell'
            try:
                resp = requests.post(url, json={'cmd': cmd, 'api_key': client.organization.api_key}, timeout=10)
                if resp.status_code == 200:
                    output = resp.text
                else:
                    output = f'Error {resp.status_code}'
            except Exception as exc:
                output = f'Failed: {exc}'
    return render_template('client_manage.html', client=client, output=output)

@main_bp.route('/organizations', methods=['GET', 'POST'])
@login_required
def organizations():
    if request.method == 'POST':
        name = request.form['name']
        org = Organization(name=name)
        db.session.add(org)
        db.session.commit()
        return redirect(url_for('main.organizations'))
    orgs = Organization.query.all()
    return render_template('organizations.html', orgs=orgs)

@main_bp.route('/organization/<int:org_id>/delete')
@login_required
def org_delete(org_id):
    org = Organization.query.get_or_404(org_id)
    for c in org.clients:
        if c.wg_public_key:
            _remove_peer(c.wg_public_key)
    db.session.delete(org)
    db.session.commit()
    return redirect(url_for('main.organizations'))

@main_bp.route('/organization/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
def org_edit(org_id):
    org = Organization.query.get_or_404(org_id)
    if request.method == 'POST':
        org.name = request.form['name']
        db.session.commit()
        return redirect(url_for('main.organizations'))
    return render_template('org_edit.html', org=org)

@main_bp.route('/plugin/<int:client_id>')
@login_required
def download_plugin(client_id):
    from io import BytesIO
    import zipfile

    client = Client.query.get_or_404(client_id)
    org = client.organization
    if not org.api_key:
        org.api_key = secrets.token_hex(16)
        db.session.commit()
    if not client.wg_private_key:
        import subprocess
        priv = subprocess.check_output(['wg', 'genkey']).decode().strip()
        pub = subprocess.check_output(['bash', '-c', f'echo {priv} | wg pubkey']).decode().strip()
        client.wg_private_key = priv
        client.wg_public_key = pub
        client.ip_address = f'10.0.0.{client.id + 10}/32'
        db.session.commit()
        _append_peer(client.wg_public_key, client.ip_address)

    mem = BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        for root, dirs, files in os.walk('ha_plugin'):
            for fname in files:
                if fname == 'client.conf' or fname == 'config.ini':
                    continue
                path = os.path.join(root, fname)
                arc = os.path.relpath(path, 'ha_plugin')
                zf.write(path, arc)

        import io, subprocess
        server_pub = ''
        pub_path = '/etc/wireguard/server_publickey'
        if os.path.exists(pub_path):
            with open(pub_path) as f:
                server_pub = f.read().strip()
        else:
            priv_path = '/etc/wireguard/server_privatekey'
            if os.path.exists(priv_path):
                with open(priv_path) as f:
                    priv = f.read().strip()
                server_pub = subprocess.check_output(['bash', '-c', f'echo {priv} | wg pubkey']).decode().strip()

        client_conf = f"""[Interface]
PrivateKey = {client.wg_private_key}
Address = {client.ip_address}

[Peer]
PublicKey = {server_pub}
Endpoint = vpn-ha-management.jayjaysrv.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        zf.writestr('client.conf', client_conf)

        cfg = configparser.ConfigParser()
        cfg['portal'] = {
            'server': 'http://ha-management.jayjaysrv.com',
            'org_id': str(org.id),
            'client_id': str(client.id),
            'api_key': org.api_key,
            'interval': '600'
        }
        buf = io.StringIO()
        cfg.write(buf)
        zf.writestr('config.ini', buf.getvalue())

    mem.seek(0)
    import re
    slug = re.sub(r'[^A-Za-z0-9]+', '_', client.name).strip('_') or f'client_{client_id}'
    return send_file(
        mem,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'HA_Plugin_{slug}.zip'
    )

@main_bp.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json() or {}
    client_id = data.get('client_id')
    api_key = data.get('api_key')
    if not client_id or not api_key:
        return '', 400
    client = Client.query.get(client_id)
    if not client or client.organization.api_key != api_key:
        return '', 403
    client.status = data.get('status', 'online')
    hostname = data.get('hostname')
    if hostname:
        client.name = hostname
    client.cpu = data.get('cpu')
    client.memory = data.get('memory')
    db.session.commit()
    return 'ok'

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        user.username = username
        if password:
            user.password = generate_password_hash(password)
        db.session.commit()
        flash('Credentials updated')
        return redirect(url_for('main.profile'))
    return render_template('profile.html')

@main_bp.route('/wireguard', methods=['GET', 'POST'])
@login_required
def wireguard():
    cfg_path = current_app.config.get('WG_CONFIG', '/etc/wireguard/wg0.conf')
    if request.method == 'POST':
        if 'remove' in request.form:
            key = request.form['remove']
            iface, peers = _parse_wg_config(cfg_path)
            peers = [p for p in peers if p.get('PublicKey') != key]
            with open(cfg_path, 'w') as f:
                f.write('[Interface]\n')
                for k, v in iface.items():
                    f.write(f'{k} = {v}\n')
                for p in peers:
                    f.write('\n[Peer]\n')
                    for k, v in p.items():
                        f.write(f'{k} = {v}\n')
            subprocess.run(['sudo', 'systemctl', 'restart', 'wg-quick@wg0'], check=False)
            return redirect(url_for('main.wireguard'))
    iface, peers = _parse_wg_config(cfg_path)
    client_map = {c.wg_public_key: c for c in Client.query.all()}
    for p in peers:
        c = client_map.get(p.get('PublicKey'))
        if c:
            p['client'] = c.name
            p['org'] = c.organization.name
    return render_template('wireguard.html', interface=iface, peers=peers)

@main_bp.route('/cloudflare', methods=['GET', 'POST'])
@login_required
def cloudflare():
    cfg_path = current_app.config.get('CF_CONFIG', 'cloudflare.ini')
    cfg = configparser.ConfigParser()
    if os.path.exists(cfg_path):
        cfg.read(cfg_path)
    labels = [('interface', 'ha-management.jayjaysrv.com'),
              ('vpn', 'vpn-ha-management.jayjaysrv.com')]
    if request.method == 'POST':
        label = request.form.get('label')
        if 'start' in request.form:
            _start_tunnel(label)
            flash(f'{label.capitalize()} tunnel gestart')
            return redirect(url_for('main.cloudflare'))
        if 'stop' in request.form:
            _stop_tunnel(label)
            flash(f'{label.capitalize()} tunnel gestopt')
            return redirect(url_for('main.cloudflare'))

        # save both tunnel configs at once
        for lbl, default_host in labels:
            host = request.form.get(f'{lbl}_hostname') or default_host
            port = request.form.get(f'{lbl}_port') or '5000'
            token = request.form.get(f'{lbl}_token', '')
            if lbl not in cfg:
                cfg[lbl] = {}
            cfg[lbl]['hostname'] = host
            cfg[lbl]['port'] = port
            cfg[lbl]['token'] = token
        with open(cfg_path, 'w') as f:
            cfg.write(f)
        flash('Configuratie opgeslagen')
        return redirect(url_for('main.cloudflare'))
    data = {}
    for label, default_host in labels:
        data[label] = {
            'hostname': cfg.get(label, 'hostname', fallback=default_host),
            'port': cfg.get(label, 'port', fallback='5000'),
            'token': cfg.get(label, 'token', fallback=''),
            'running': _tunnel_running(label),
        }
    return render_template('cloudflare.html', config=data)

@main_bp.route('/init')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
    return 'Initialized.'
