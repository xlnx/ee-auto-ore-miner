import logging
from random import randint
from game_window import GameWindow
from idler import IdleState, Idler
from miner import MineState, Miner
from typing import List, Tuple
from ore import Ore
from config import config
from util import now_sec, sleep

MAX_MINER_RANGE = 19

prev_t = 0
start_time = now_sec()


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

    def idle(self, docked: bool) -> IdleState:
        if not docked:
            t = now_sec() - start_time
            global prev_t
            dt = t - prev_t
            if dt >= 40:
                prev_t = t
                self._wnd.open(config.overview.ores)
                targets = self._wnd.list_fast(3)
                cnt = len(targets)
                if cnt > 0:
                    self._wnd.target_op(0, 1)
                else:
                    return IdleState.Deploy
        return self._idler.idle(self._wnd, docked=docked)
