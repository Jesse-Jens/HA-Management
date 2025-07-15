import os
import secrets
import configparser
import subprocess
import psutil
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

@main_bp.route('/client/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    # placeholder for real management features
    return render_template('client.html', client=client)

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
Endpoint = homeassistant.jayjaysrv.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        zf.writestr('client.conf', client_conf)

        cfg = configparser.ConfigParser()
        cfg['portal'] = {
            'server': 'http://homeassistant.jayjaysrv.com',
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
    return render_template('wireguard.html', interface=iface, peers=peers)

@main_bp.route('/init')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
    return 'Initialized.'
