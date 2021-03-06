import logging
from typing import List, Tuple
from .config import config
from .idler import Idler
from .miner import MineState, Miner
from .ore import Ore
from .util import sleep
from .client import Client

MAX_MINER_RANGE = 19


def sort_ore_targets(ores) -> List[int]:
    ores = [
        (i, d, o)
        for i, (d, o) in enumerate(ores)
        if o != Ore.Unknown  # and d <= MAX_MINER_RANGE
    ]
    ores = sorted(
        ores,
        key=lambda x: (-x[2].market_price_per_volume, x[1])
    )
    targets = [i for i, _, _ in ores]
    return targets


class LaserMiner(Miner):
    def __init__(self, window: Client, idler: Idler) -> None:
        self._wnd = window
        self._idler = idler

    def apply(self, ores: List[Tuple[float, Ore]]) -> MineState:
        targets = sort_ore_targets(ores)
        if len(targets) == 0:
            return MineState.Fail
        logging.info('optimal targets: %s', [ores[i] for i in targets])
        idx = targets[0]
        d, _ = ores[idx]
        self._wnd.target_op(0, 1)
        if d <= MAX_MINER_RANGE:
            self._wnd.unlock_all()
            # for idx in targets:
            self._wnd.lock(idx, 2000)
            for row, col in config.devices.miners:
                self._wnd.activate_device(row, col)
            # wnd_orbit_target(targets[0], 2)
            return MineState.Success
        # wnd_orbit_target(0, 2)
        # wnd_orbit_target(idx)
        di = 9999
        while di >= MAX_MINER_RANGE:
            targets = self._wnd.list()
            if len(targets) == 0:
                return MineState.Fail
            di, _ = targets[0]
            logging.info('d = %f km', di)
            sleep(1000)
        return MineState.Retry

    def idle(self, docked: bool) -> None:
        self._idler.idle(self._wnd, docked=docked)
