import logging
import socketio
from collections import deque
from typing import Any, Deque, Dict, Optional, Tuple
from .window import Window


class Admin():
    def __init__(self,
                 window: Window,
                 role: str,
                 user_id: str,
                 addr: Optional[str] = None) -> None:
        self._queue = deque()
        self._sio = socketio.Client()
        device = {
            'id': user_id,
            'serial': window.serial,
            'product': {
                'model': window.shell('getprop ro.product.model'),
                'manufacturer': window.shell('getprop ro.product.manufacturer'),
                'abi': window.shell('getprop ro.product.cpu.abi'),
            },
            'soc': {
                'manufacturer': window.shell('getprop ro.soc.manufacturer'),
                'model': window.shell('getprop ro.soc.model'),
            }
        }
        self._state = {}
        self._data = {'device': device, 'state': self._state}

        def slave_task(name, *args):
            self._queue.append((name, args))
        self._sio.event(slave_task)

        def connect():
            self.emit('init', role, self._data)
        self._sio.event(connect)

        url = f'http://{addr}'
        try:
            self._sio.connect(url, wait_timeout=1)
        except Exception as e:
            logging.warning(f'connect to admin failed: {url}')
            self._sio = None
            return

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    @property
    def tasks(self) -> Deque[Tuple[str, Any]]:
        return self._queue

    def emit(self, event: str, *args):
        if self._sio is not None:
            try:
                self._sio.emit('dispatch', (event, *args))
            except Exception:
                pass

    def update(self, key: str, value: Any):
        self.state[key] = value
        self.emit('update', key, value)

    def heartbeat(self):
        self.emit('heartbeat')

    def disconnect(self):
        if self._sio is not None:
            self._sio.disconnect()
