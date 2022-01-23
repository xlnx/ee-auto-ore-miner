from config import config
from idler import Idler
from util import sleep
from window import Window


class OverviewPiratesIdler(Idler):
    def idle(self, window: Window) -> None:
        window.open(config.overview.pirates)
        targets = window.list_fast(1)
        if len(targets) > 0:
            window.fast_dock()
            window.discharge_storage()
            sleep(1000 * config.idler.get("dock_time_sec", 60 * 3))
            window.undock()
            return True
        return False
