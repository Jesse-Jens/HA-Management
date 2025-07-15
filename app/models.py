from . import db, login_manager
from flask_login import UserMixin

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    status = db.Column(db.String(50))
    ip_address = db.Column(db.String(20), unique=True)
    wg_private_key = db.Column(db.Text)
    wg_public_key = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    api_key = db.Column(db.String(64), unique=True)
    clients = db.relationship('Client', backref='organization', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='admin')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
