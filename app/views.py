from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from .models import Client, User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

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

@main_bp.route('/init')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
    return 'Initialized.'
