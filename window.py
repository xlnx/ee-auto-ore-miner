import io
from config import config
from ppadb.client import Client as AdbClient
from PIL import Image
from util import sleep


ACTION_INTERVAL_MS = 300


class Window():
    def __init__(self) -> None:
        client = AdbClient(host='127.0.0.1', port=5037)
        client.remote_connect(config.server.host, config.server.port)
        devices = client.devices()
        self._adb = devices[0]
        self._x, self._y = self._adb.wm_size()
        assert (self._x, self._y) == (1600, 900)

    # def __del__(self):
    #     self.

    @property
    def width(self) -> int:
        return self._x

    @property
    def height(self) -> int:
        return self._y

    def screenshot(self, rect=None) -> Image:
        cap = self._adb.screencap()
        im = Image.open(io.BytesIO(cap)).convert('RGB')
        if rect is not None:
            return im.crop(rect)
        return im

    def tap(self, x: int, y: int, dt: int = ACTION_INTERVAL_MS) -> None:
        self._adb.shell(f'input tap {x} {y}')
        sleep(dt)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500, dt: int = ACTION_INTERVAL_MS) -> None:
        self._adb.shell(f'input swipe {x1} {y1} {x2} {y2} {duration}')
        sleep(duration + dt)

    def shell(self, cmd: str):
        return self._adb.shell(cmd)
