from idler import IdleState, Idler
from game_window import GameWindow


class LocalPiratesIdler(Idler):
    def idle(self, window: GameWindow) -> IdleState:
        return IdleState.Nothing
        # window.open(config.overview.pirates)
        # targets = window.list_fast(1)
        # if len(targets) > 0:
        #     window.dock()
        #     sleep(1000 * 60 * 3)
        #     window.undock()
