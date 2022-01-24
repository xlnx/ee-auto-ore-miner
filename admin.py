import json
import logging
import socketio
from typing import Any, Deque, Tuple
from collections import deque
from config import config

with open('admin.json', encoding='utf-8') as f:
    _CONFIG = json.load(f)
HOST = _CONFIG['host']
PORT = _CONFIG['port']


class Admin():
    def __init__(self, adb) -> None:
        self._queue = deque()
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
            'product': {
                'model': adb.shell('getprop ro.product.model'),
                'manufacturer': adb.shell('getprop ro.product.manufacturer'),
                'abi': adb.shell('getprop ro.product.cpu.abi'),
            },
            'soc': {
                'manufacturer': adb.shell('getprop ro.soc.manufacturer'),
                'model': adb.shell('getprop ro.soc.model'),
            }
        }
        self.emit('slave_init', server)

        def slave_task(name, *args):
            self._queue.append((name, args))
        self._sio.event(slave_task)

    @property
    def tasks(self) -> Deque[Tuple[str, Any]]:
        return self._queue

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
