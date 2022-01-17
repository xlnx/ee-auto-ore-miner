import logging
from random import randint
from game_window import GameWindow
from idler import Idler
from miner import MineState, Miner
from typing import List, Tuple
from ore import Ore
from config import config
from util import sleep

MAX_MINER_RANGE = 19


class StripMiner(Miner):
    def __init__(self, window: GameWindow, idler: Idler) -> None:
        self._wnd = window
        self._idler = idler

    def apply(self, ores: List[Tuple[float, Ore]]) -> MineState:
        self._wnd.approach(0)
        if config.devices.contains('thruster'):
            row, col = config.devices.thruster
            self._wnd.activate(row, col)
            # self._wnd.activate(row, col)
        di = 9999
        while di >= MAX_MINER_RANGE:
            targets = self._wnd.list()
            if len(targets) == 0:
                return MineState.Fail
            di = targets[0].distance
            logging.info('d = %f km', di)
            sleep(1000)
        for row, col in config.devices.miners:
            self._wnd.activate(row, col)
        return MineState.Success

    def idle(self) -> None:
        self._idler.idle(self._wnd)
