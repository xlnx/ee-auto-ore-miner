import io
from config import config
from adbutils import adb
from PIL import Image
from util import sleep


adb.connect(config.server.host + ":" + str(config.server.port))

ACTION_INTERVAL_MS = 300


class Window():
    def __init__(self) -> None:
        self._adb = adb.devices()[0]
        self._y, self._x = self._adb.window_size()
        assert (self._x, self._y) == (1600, 900)

    @property
    def width(self) -> int:
        return self._x

    @property
    def height(self) -> int:
        return self._y

    def screenshot(self, rect=None) -> Image:
        cmd = "screencap -p"
        stream = self._adb.shell(cmd, stream=True)
        result = b''
        while True:
            N = 2048
            buf = stream.read(N)
            result += buf
            if len(buf) != N:
                break
        if result and len(result) > 5 and result[5] == 0x0d:
            cap = result.replace(b'\r\n', b'\n')
        else:
            cap = result
        im = Image.open(io.BytesIO(cap)).convert('RGB')
        if rect is not None:
            return im.crop(rect)
        return im

    def tap(self, x: int, y: int, dt: int = ACTION_INTERVAL_MS) -> None:
        self._adb.click(x, y)
        sleep(dt)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500, dt: int = ACTION_INTERVAL_MS) -> None:
        self._adb.swipe(x1, y1, x2, y2, duration * 1e-3)
        sleep(duration + dt)

    def shell(self, cmd: str):
        return self._adb.shell(cmd)
