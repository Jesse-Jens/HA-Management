import os
import requests
import socket
import time

SERVER = os.environ.get('PORTAL', 'http://homeassistant.jayjaysrv.com')
ORG_ID = os.environ.get('ORG_ID')

while True:
    try:
        data = {
            'hostname': socket.gethostname(),
            'status': 'online',
            'org_id': ORG_ID,
        }
        requests.post(f"{SERVER}/api/heartbeat", json=data, timeout=5)
    except Exception:
        pass
    time.sleep(60)
