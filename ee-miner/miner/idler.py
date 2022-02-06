from enum import Enum
from .client import Client


class IdleState(Enum):
    Nothing = 0
    Deploy = 1


class Idler():
    def idle(self, window: Client, docked: bool) -> IdleState:
        return IdleState.Nothing
