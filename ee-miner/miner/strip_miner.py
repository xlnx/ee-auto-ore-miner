import time
from typing import List, Tuple
from .idler import IdleState, Idler
from .miner import MineState, Miner
from .ore import Ore
from .config import config
from .client import Client

MAX_MINER_RANGE = 19

prev_t = 0
start_time = time.time()


class StripMiner(Miner):
    def __init__(self, window: Client, idler: Idler) -> None:
        self._wnd = window
        self._idler = idler

    def apply(self, ores: List[Tuple[float, Ore]]) -> MineState:
        self._wnd.overview.target_op(0, 1)
        if config.devices.contains('thruster'):
            row, col = config.devices.thruster
            self._wnd.activate_device(row, col)
            self._wnd.activate_device(row, col)
        for row, col in config.devices.miners:
            self._wnd.activate_device(row, col)
        return MineState.Success

    def idle(self, docked: bool) -> IdleState:
        if not docked:
            t = time.time() - start_time
            global prev_t
            dt = t - prev_t
            if dt >= 40:
                prev_t = t
                self._wnd.overview.open(config.overview.ores)
                targets = self._wnd.overview.list_fast(3)
                cnt = len(targets)
                if cnt > 0:
                    self._wnd.overview.target_op(0, 1)
                else:
                    return IdleState.Deploy
        return self._idler.idle(self._wnd, docked=docked)
