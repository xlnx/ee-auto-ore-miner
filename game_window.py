from local import Local
from window import Window
from panel import Panel
from overview import Overview


class GameWindow(Window, Panel, Overview, Local):
    def __init__(self) -> None:
        Window.__init__(self)
        Panel.__init__(self)
        Overview.__init__(self)
        Local.__init__(self)
