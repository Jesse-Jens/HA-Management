import os
import requests
import socket
import time
import configparser

cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
portal = cfg['portal']

SERVER = portal.get('server', 'http://homeassistant.jayjaysrv.com')
ORG_ID = portal.get('org_id', '')
API_KEY = portal.get('api_key', '')
INTERVAL = int(portal.get('interval', '600'))

while True:
    try:
        data = {
            'hostname': socket.gethostname(),
            'status': 'online',
            'org_id': ORG_ID,
            'api_key': API_KEY,
        }
        requests.post(f"{SERVER}/api/heartbeat", json=data, timeout=5)
    except Exception:
        pass
    time.sleep(INTERVAL)
