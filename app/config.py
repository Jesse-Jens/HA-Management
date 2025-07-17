import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
    BASEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_PATH = os.path.join(BASEDIR, 'management.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WG_CONFIG = '/etc/wireguard/wg0.conf'
    CF_CONFIG = os.path.join(BASEDIR, 'cloudflare.ini')
