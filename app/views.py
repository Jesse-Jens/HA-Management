from flask import Blueprint, render_template, request, redirect, url_for, Response
from flask_login import login_user, login_required, logout_user, current_user
from .models import Client, User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import json
import requests

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    clients = Client.query.all()
    return render_template('dashboard.html', clients=clients)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
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
    clients = Client.query.filter(Client.name.contains(q)).all()
    return render_template('clients.html', clients=clients, q=q)

@main_bp.route('/client/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    # placeholder for real management features
    return render_template('client.html', client=client)

@main_bp.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def client_edit(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.location = request.form['location']
        client.status = request.form['status']
        client.ha_token = request.form.get('ha_token')
        db.session.commit()
        return redirect(url_for('main.client_detail', client_id=client.id))
    return render_template('client_edit.html', client=client)

@main_bp.route('/client/<int:client_id>/manage')
@login_required
def client_manage(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('client_manage.html', client=client)

@main_bp.route('/client/<int:client_id>/action', methods=['POST'])
@login_required
def client_action(client_id):
    client = Client.query.get_or_404(client_id)
    path = request.form['path']
    payload = request.form.get('payload')
    url = f"http://{client.location}:8123/api/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {client.ha_token}"}
    data = None
    if payload:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = payload
    try:
        r = requests.post(url, headers=headers, json=data)
        output = r.text
    except Exception as e:
        output = str(e)
    return render_template('client_manage.html', client=client, output=output)

@main_bp.route('/client/<int:client_id>/download')
@login_required
def download_plugin(client_id):
    client = Client.query.get_or_404(client_id)
    wg_conf = f"[Interface]\nPrivateKey = <private>\nAddress = 10.0.0.{client.id}/32\n\n[Peer]\nEndpoint = {request.host.split(':')[0]}:51820\nAllowedIPs = 0.0.0.0/0\n"
    return Response(wg_conf, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename=client-{client.id}-wg.conf'})

@main_bp.route('/init')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
    return 'Initialized.'
