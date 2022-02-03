from config import config
from idler import IdleState, Idler
from util import sleep
from game_window import GameWindow


class OverviewPiratesIdler(Idler):
    def idle(self, window: GameWindow) -> IdleState:
        window.open(config.overview.pirates)
        targets = window.list_fast(1)
        if len(targets) > 0:
            targets = window.list_fast(1)
            if len(targets) > 0:
                window.dock()
                window.discharge_storage()
                for _ in range(config.idler.get("dock_time_sec", 60 * 3)):
                    window.admin.heartbeat()
                    # while len(window.admin.tasks):
                    # name, args = window.admin.tasks.pop()
                    # if name == 'offline':

                    # # if not apply_task(False, name, *args):
                    # #     return
                    sleep(1000)
                window.undock()
                return IdleState.Deploy
        return IdleState.Nothing
