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
        self._wnd.target_op(0, 1)
        if config.devices.contains('thruster'):
            row, col = config.devices.thruster
            self._wnd.activate(row, col)
            self._wnd.activate(row, col)
        for row, col in config.devices.miners:
            self._wnd.activate(row, col)
        return MineState.Success

    def idle(self) -> None:
        self._idler.idle(self._wnd)
