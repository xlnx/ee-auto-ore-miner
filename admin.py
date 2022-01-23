import logging
from typing import Any
import socketio
import json
from config import config

with open('admin.json', encoding='utf-8') as f:
    _CONFIG = json.load(f)
HOST = _CONFIG['host']
PORT = _CONFIG['port']


class Admin():
    def __init__(self) -> None:
        self._sio = socketio.Client()
        url = f'http://{HOST}:{PORT}'
        try:
            self._sio.connect(url, wait_timeout=1)
        except Exception as e:
            logging.warning(f'connect to admin failed: {url}')
            self._sio = None
        server = {
            'host': config.server.host,
            'port': config.server.port,
        }
        self.emit('slave_init', server)

    def emit(self, event: str, data: Any):
        if self._sio is not None:
            self._sio.emit(event, data)

    def heartbeat(self):
        if self._sio is not None:
            self._sio.emit('heartbeat')

    def disconnect(self):
        if self._sio is not None:
            self._sio.disconnect()


if __name__ == '__main__':
    admin = Admin()
