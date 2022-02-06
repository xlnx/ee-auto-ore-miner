import time
import logging
from typing import Tuple
from .config import config
from .idler import IdleState, Idler
from .util import sleep
from .client import Client


class OverviewPiratesIdler(Idler):
    def idle(self, window: Client, docked: bool) -> IdleState:
        emergency = 0
        if not docked:
            window.overview.open(config.overview.pirates)
            targets = window.overview.list_fast(1)
            if len(targets) > 0:
                targets = window.overview.list_fast(1)
                if len(targets) > 0:
                    logging.warn('emergency.targets: %s', targets)
                    emergency = 1
        if not emergency:
            x, y, z = window.local.count()
            window.admin.emit('update_local', (x, y, z))
            th = config.get('max_local_rivals', 0)
            if x + y > th:
                logging.warn('emergency.local: %s > %d', [x, y, z], th)
                emergency = 2
        if emergency:
            def idle() -> Tuple[int, int, int]:
                xs = window.local.count()
                window.admin.emit('update_local', xs)
                window.admin.heartbeat()
                sleep(1000)
                return xs

            if not docked:
                window.dock()
                window.discharge_storage()
            if emergency == 1:
                dt = config.idler.get("dock_time_sec", 60 * 3)
                t = time.time()
                while True:
                    idle()
                    if time.time() - t >= dt:
                        break
            th = config.get('max_local_rivals', 0)
            while True:
                x, y, z = idle()
                if x + y <= th:
                    logging.warn('~emergency.local: %s <= %d', [x, y, z], th)
                    break
            if not docked:
                window.undock()
                return IdleState.Deploy
        return IdleState.Nothing
