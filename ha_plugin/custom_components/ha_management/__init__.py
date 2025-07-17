import logging
import socket
from datetime import timedelta
import requests
import configparser
import os

DOMAIN = "ha_management"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    cfg = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')
    path = os.path.abspath(path)
    if os.path.exists(path):
        cfg.read(path)
        portal = cfg['portal']
    else:
        portal = {
            'server': os.environ.get('SERVER', 'http://homeassistant.jayjaysrv.com'),
            'org_id': os.environ.get('ORG_ID', ''),
            'client_id': os.environ.get('CLIENT_ID', ''),
            'api_key': os.environ.get('API_KEY', ''),
            'interval': os.environ.get('INTERVAL', '600'),
        }

    server = portal.get('server')
    org_id = portal.get('org_id')
    client_id = portal.get('client_id')
    api_key = portal.get('api_key')
    interval = int(portal.get('interval', '600'))

    if not org_id:
        _LOGGER.error("Organization id missing")
        return False

    def send_heartbeat(event_time):
        data = {
            'hostname': socket.gethostname(),
            'status': 'online',
            'org_id': org_id,
            'client_id': client_id,
            'api_key': api_key,
        }
        try:
            requests.post(f"{server}/api/heartbeat", json=data, timeout=5)
        except Exception as exc:
            _LOGGER.warning("Heartbeat failed: %s", exc)

    hass.helpers.event.track_time_interval(send_heartbeat, timedelta(seconds=interval))
    return True
