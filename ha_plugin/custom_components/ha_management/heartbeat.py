import socket
import time
import requests
import configparser
import os
import psutil
import subprocess
from flask import Flask, request
import threading

CONFIG = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')

cfg = configparser.ConfigParser()
cfg.read(CONFIG)
portal = cfg['portal']
SERVER = portal.get('server', 'http://homeassistant.jayjaysrv.com')
ORG_ID = portal.get('org_id', '')
CLIENT_ID = portal.get('client_id', '')
API_KEY = portal.get('api_key', '')
INTERVAL = int(portal.get('interval', '600'))

app = Flask(__name__)

@app.route('/action', methods=['POST'])
def action():
    if request.json.get('api_key') != API_KEY:
        return 'unauthorized', 403
    cmd = request.json.get('cmd')
    if cmd == 'reboot':
        subprocess.Popen(['sudo', 'reboot'])
    elif cmd == 'shutdown':
        subprocess.Popen(['sudo', 'shutdown', '-h', 'now'])
    return 'ok'

def run_server():
    app.run(host='0.0.0.0', port=5001)

threading.Thread(target=run_server, daemon=True).start()

while True:
    payload = {
        'hostname': socket.gethostname(),
        'status': 'online',
        'org_id': ORG_ID,
        'client_id': CLIENT_ID,
        'api_key': API_KEY,
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
    }
    try:
        requests.post(f"{SERVER}/api/heartbeat", json=payload, timeout=5)
    except Exception:
        pass
    time.sleep(INTERVAL)
