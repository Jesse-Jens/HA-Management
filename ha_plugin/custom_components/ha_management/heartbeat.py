import socket
import time
import requests
import configparser
import os

CONFIG = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')

cfg = configparser.ConfigParser()
cfg.read(CONFIG)
portal = cfg['portal']
SERVER = portal.get('server', 'http://homeassistant.jayjaysrv.com')
ORG_ID = portal.get('org_id', '')
API_KEY = portal.get('api_key', '')
INTERVAL = int(portal.get('interval', '600'))

while True:
    payload = {
        'hostname': socket.gethostname(),
        'status': 'online',
        'org_id': ORG_ID,
        'api_key': API_KEY,
    }
    try:
        requests.post(f"{SERVER}/api/heartbeat", json=payload, timeout=5)
    except Exception:
        pass
    time.sleep(INTERVAL)
