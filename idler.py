from enum import Enum
from game_window import GameWindow


class IdleState(Enum):
    Nothing = 0
    Deploy = 1


class Idler():
    def idle(self, window: GameWindow, docked: bool) -> IdleState:
        return IdleState.Nothing
