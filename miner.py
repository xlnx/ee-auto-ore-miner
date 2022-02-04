from enum import Enum
from typing import List, Tuple

from ore import Ore


class MineState(Enum):
    Fail = 0
    Success = 1
    Retry = 2


class Miner():
    def apply(self, ores: List[Tuple[float, Ore]]) -> MineState:
        pass

    def idle(self, docked: bool) -> None:
        pass
