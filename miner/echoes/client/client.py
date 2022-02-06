import cv2
import atexit
import logging
import numpy as np
from typing import Optional
from .local import Local
from .overview import Overview
from .window import Window
from .admin import Admin
from .util import is_similar, ocr, parse_prefix_float, sleep, try_again, get_static

OVERVIEW_IND = cv2.imread(get_static("overview.png"))


class AdbClient(Window):
    def __init__(self,
                 serial: str,
                 role: str = 'Slave',
                 admin_addr: Optional[str] = None,
                 user_id: str = '<匿名>') -> None:
        Window.__init__(self, serial=serial)
        self._admin = Admin(self,
                            role=role,
                            user_id=user_id,
                            addr=admin_addr)
        self._overview = Overview(self)
        self._local = Local(self)

        atexit.register(lambda: self._admin.disconnect())

    @property
    def admin(self) -> Admin:
        return self._admin

    @property
    def overview(self) -> Overview:
        return self._overview

    @property
    def local(self) -> Local:
        return self._local

    def get_system_name(self) -> str:
        img = self.screenshot(
            (self.y(175), self.y(30), self.y(260), self.y(52)))
        system = ocr(img, cand_alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
                     single_line=True)
        return system

    def try_get_navigate_speed(self) -> float:
        x_2 = self.width / 2
        dx = self.y(110)
        img = self.screenshot(
            (x_2 - dx, self.height - self.y(55), x_2 + dx, self.height - self.y(29)))
        speed = ocr(img, cand_alphabet="0123456789.,/千米秒天文单位",
                    single_line=True)
        speed = speed.replace(',', '')
        logging.debug('speed %s', speed)
        unit = 1
        if '单位' in speed or '天' in speed:
            unit = 149597870700.0
        elif '千' in speed:
            unit = 1000.0
        elif '米' in speed:
            unit = 1.0
        else:
            raise NotImplementedError()
        speed = parse_prefix_float(speed) * unit
        logging.debug('current speed is %s m/s', speed)
        return speed

    # ok
    @try_again
    def get_navigate_speed(self) -> float:
        return self.try_get_navigate_speed()

    def try_get_storage_percent(self) -> float:
        img = self.screenshot(
            (self.y(40), self.y(130), self.y(118), self.y(155)))
        perc = ocr(img, cand_alphabet="0123456789.%", single_line=True)
        logging.debug('storage %s', perc)
        x, y = 420, 145
        if len(perc) == 0 or perc[-1] != '%':
            self.tap(self.y(x), self.y(y))
            raise NotImplementedError()
        val = parse_prefix_float(perc)
        if val > 100:
            self.tap(self.y(x), self.y(y))
            raise NotImplementedError()
        return val

    # ok
    @try_again
    def get_storage_percent(self) -> float:
        return self.try_get_storage_percent()

    # ok
    def activate_device(self, row: int, col: int = 0, dt: int = 300) -> None:
        self.tap(
            self.width - self.y(68) - row * self.y(101),
            self.height - self.y(72) - col * self.y(105), dt)
        sleep(50)

    def is_device_active(self, row: int, col: int = 0) -> None:
        img = self.screenshot()
        x = self.width - 66 - row * 101
        y = self.height - 110 - col * 105
        rgb = img.getpixel((x, y))
        if is_similar(rgb, (220, 220, 220), 40):
            logging.debug("active found: (%d, %d) %s", x, y, rgb)
            return True
        return False

    # ok
    def is_docked(self) -> bool:
        y = self.y(290)
        xs = [self.y(_) for _ in [176., 204., 228.]]
        pts = [(x, y) for x in xs]
        img = self.screenshot()
        xs = [img.getpixel((self.width - x, y)) for x, y in pts]
        return all(is_similar(x, (174, 147, 40), 10) for x in xs)

    # ok
    def _is_undocked(self) -> bool:
        x = self.width / 2
        img = self.screenshot((x, 0, self.width, self.height))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(
            img, OVERVIEW_IND, cv2.TM_CCOEFF_NORMED)
        dy, dx = np.unravel_index(result.argmax(), result.shape)
        return x - dx < self.y(100) and dy > self.y(450) and dy < self.y(500)

    # ok
    def undock(self) -> None:
        self.admin.update('status', 'undocking')
        logging.info('undock')
        self.tap(self.width - self.y(108), self.y(300))
        while True:
            if self._is_undocked():
                sleep(4000)
                break
        self.tap(self.width - self.y(64), self.y(506))
        # self.tap(self.width / 2, self.height - 180)
        sleep(2000)
        logging.info('undocked')
        self.admin.update('status', 'undocked')
