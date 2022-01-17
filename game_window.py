from window import Window
from panel import Panel
from overview import Overview


class GameWindow(Window, Panel, Overview):
    def __init__(self) -> None:
        Window.__init__(self)
        Panel.__init__(self)
        Overview.__init__(self)
