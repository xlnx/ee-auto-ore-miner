from idler import Idler
from window import Window


class LocalPiratesIdler(Idler):
    def idle(self, window: Window) -> None:
        pass
        # window.open(config.overview.pirates)
        # targets = window.list_fast(1)
        # if len(targets) > 0:
        #     window.fast_dock()
        #     sleep(1000 * 60 * 3)
        #     window.undock()
