import logging
from config import config
from idler import IdleState, Idler
from util import sleep
from game_window import GameWindow


class OverviewPiratesIdler(Idler):
    def idle(self, window: GameWindow, docked: bool) -> IdleState:
        emergency = 0
        if not docked:
            window.open(config.overview.pirates)
            targets = window.list_fast(1)
            if len(targets) > 0:
                targets = window.list_fast(1)
                if len(targets) > 0:
                    logging.warn('emergency.targets: %s', targets)
                    emergency = 1
        if not emergency:
            x, y, z = window.get_local_count()
            window.admin.emit('update_local', (x, y, z))
            th = config.get('max_local_rivals', 0)
            if x + y > th:
                logging.warn('emergency.local: %s > %d', [x, y, z], th)
                emergency = 2
        if emergency:
            def idle():
                window.admin.heartbeat()
                # while len(window.admin.tasks):
                # name, args = window.admin.tasks.pop()
                # if name == 'offline':

                # # if not apply_task(False, name, *args):
                # #     return
                sleep(1000)

            if not docked:
                window.dock()
                window.discharge_storage()
            if emergency == 1:
                for _ in range(config.idler.get("dock_time_sec", 60 * 3)):
                    idle()
            th = config.get('max_local_rivals', 0)
            while True:
                x, y, z = window.get_local_count()
                window.admin.emit('update_local', (x, y, z))
                if x + y <= th:
                    logging.warn('~emergency.local: %s <= %d', [x, y, z], th)
                    break
                idle()
            if not docked:
                window.undock()
                return IdleState.Deploy
        return IdleState.Nothing
