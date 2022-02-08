import io
import logging
from typing import Optional
from PIL import Image
from adbutils import adb
from .util import sleep


class Window():
    def __init__(self,
                 serial: Optional[str] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None) -> None:
        if serial is None:
            assert host is not None and port is not None
            serial = f'{host}:{port}'
            adb.connect(serial)
        self._serial = serial
        self._adb = adb.device(serial=serial)
        x, y = self._adb.window_size()
        if x < y:
            x, y = y, x
        logging.info("device [%s] resolution: %dx%d", serial, x, y)
        self._x, self._y = x, y

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def width(self) -> int:
        return self._x

    @property
    def height(self) -> int:
        return self._y

    def x(self, x: int) -> int:
        x1 = round(self._x * float(x) / 1600)
        x1 = max(0, min(self._x, x1))
        return x1

    def y(self, y: int) -> int:
        y1 = round(self._y * float(y) / 900)
        y1 = max(0, min(self._y, y1))
        return y1

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

    def tap(self, x: int, y: int, dt: int = 300) -> None:
        self._adb.click(x, y)
        sleep(dt)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500, dt: int = 300) -> None:
        self._adb.swipe(x1, y1, x2, y2, duration * 1e-3)
        sleep(duration + dt)

    def shell(self, cmd: str):
        return self._adb.shell(cmd)
