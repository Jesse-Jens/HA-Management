import os
import secrets
import configparser
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_user, login_required, logout_user, current_user
from .models import Client, User, Organization
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

main_bp = Blueprint('main', __name__)

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
    return render_template('dashboard.html', clients=clients, orgs=orgs, counts=counts)

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

@main_bp.route('/plugin/<int:org_id>')
@login_required
def download_plugin(org_id):
    from io import BytesIO
    import zipfile

    org = Organization.query.get_or_404(org_id)
    if not org.api_key:
        org.api_key = secrets.token_hex(16)
        db.session.commit()

    mem = BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        for root, dirs, files in os.walk('ha_plugin'):
            for fname in files:
                path = os.path.join(root, fname)
                arc = os.path.relpath(path, 'ha_plugin')
                zf.write(path, arc)

        cfg = configparser.ConfigParser()
        cfg['portal'] = {
            'server': 'http://homeassistant.jayjaysrv.com',
            'org_id': str(org.id),
            'api_key': org.api_key,
            'interval': '600'
        }
        import io
        buf = io.StringIO()
        cfg.write(buf)
        zf.writestr('config.ini', buf.getvalue())

    mem.seek(0)
    return send_file(mem, mimetype='application/zip', as_attachment=True,
                     download_name=f'ha_plugin_org_{org_id}.zip')

@main_bp.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json() or {}
    name = data.get('hostname')
    org_id = data.get('org_id')
    if not name:
        return '', 400
    client = Client.query.filter_by(name=name, organization_id=org_id).first()
    if not client:
        client = Client(name=name, organization_id=org_id)
        db.session.add(client)
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
        with open(cfg_path, 'w') as f:
            f.write(request.form['config'])
        os.system('sudo systemctl restart wg-quick@wg0 >/dev/null 2>&1')
        flash('WireGuard configuration updated')
        return redirect(url_for('main.wireguard'))
    try:
        with open(cfg_path) as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
    return render_template('wireguard.html', config=content)

@main_bp.route('/init')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
    return 'Initialized.'
