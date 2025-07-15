import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WG_CONFIG = '/etc/wireguard/wg0.conf'
