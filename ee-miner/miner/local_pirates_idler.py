from .idler import IdleState, Idler
from .client import Client


class LocalPiratesIdler(Idler):
    def idle(self, window: Client) -> IdleState:
        return IdleState.Nothing
        # window.open(config.overview.pirates)
        # targets = window.list_fast(1)
        # if len(targets) > 0:
        #     window.dock()
        #     sleep(1000 * 60 * 3)
        #     window.undock()
