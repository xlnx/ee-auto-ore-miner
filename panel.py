import cv2
import logging
import numpy as np
from contextlib import contextmanager
from util import is_similar, now_sec, ocr, parse_prefix_float, sleep, try_again


CURRENT_SHIP_IND = cv2.imread("current_ship.png")
OVERVIEW_IND = cv2.imread("overview.png")


class Panel():
    def __init__(self) -> None:
        pass

    @try_again
    def get_navigate_speed(self) -> float:
        img = self.screenshot(
            (688, self.height - 55, 910, self.height - 29))
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

    @try_again
    def get_storage_percent(self) -> float:
        img = self.screenshot((40, 130, 118, 155))
        perc = ocr(img, cand_alphabet="0123456789.%", single_line=True)
        logging.debug('storage %s', perc)
        if perc[-1] != '%':
            raise NotImplementedError()
        val = parse_prefix_float(perc)
        if val > 100:
            raise NotImplementedError()
        return val

    def unlock_all(self) -> None:
        logging.debug('unlock all')
        for i in range(1)[::-1]:
            x = self.width - 481 - 103 * i
            y = 65
            self.swipe(x, y, x + 5, y + 300)
        sleep(3000)

    def activate(self, row: int, col: int = 0) -> None:
        self.tap(
            self.width - 68 - row * 101,
            self.height - 72 - col * 105)
        sleep(50)

    def is_active(self, row: int, col: int = 0) -> None:
        img = self.screenshot()
        x = self.width - 66 - row * 101
        y = self.height - 110 - col * 105
        rgb = img.getpixel((x, y))
        if is_similar(rgb, (220, 220, 220), 40):
            logging.debug("active found: (%d, %d) %s", x, y, rgb)
            return True
        return False

    def is_docked(self) -> bool:
        pts = [
            (176, 290),
            (204, 290),
            (228, 290),
        ]
        img = self.screenshot()
        xs = [img.getpixel((self.width - x, y)) for x, y in pts]
        return all(is_similar(x, (174, 147, 40), 10) for x in xs)

    def is_undocked(self) -> bool:
        img = self.screenshot((800, 0, 1600, 900))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(
            img, OVERVIEW_IND, cv2.TM_CCOEFF_NORMED)
        dy, dx = np.unravel_index(result.argmax(), result.shape)
        return dx > 700 and dy > 450 and dy < 500

    def undock(self) -> None:
        self.tap(self.width - 108, 300)
        while True:
            if self.is_undocked():
                sleep(4000)
                break
        self.tap(self.width - 64, 506)
        self.tap(self.width / 2, self.height - 180)
        sleep(2000)

    @contextmanager
    def open_wirehouse(self) -> None:
        logging.debug('open wirehouse')
        self.tap(10, 10)
        sleep(1000)
        self.tap(420, 420)
        sleep(3000)
        yield
        self.tap(self.width - 60, 50)
        sleep(3000)

    def discharge_storage(self) -> None:
        logging.debug('discharge storage')
        x, y = 15, 100
        w, h = 315, 700
        while True:
            img = self.screenshot((x, y, x + w, y + h))
            img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(
                img, CURRENT_SHIP_IND, cv2.TM_CCOEFF_NORMED)
            dy, dx = np.unravel_index(result.argmax(), result.shape)
            logging.info('(%d, %d)', dx, dy)
            if dx <= 15 and dy + 300 < h:
                break
            y1, y2 = 200, 50
            logging.info('need swipe: %d -> %d', y1, y2)
            self.swipe(180, y1, 180, y2, 1000)
            sleep(2000)
        logging.debug('detected current ship: (%d, %d)', x, y)
        x, y = x + dx + 288, y + dy + 100
        self.tap(x, y)
        self.tap(x, y)
        self.tap(x - 140, y + 60)
        sleep(2000)
        self.tap(self.width - 370, self.height - 80)
        sleep(2000)
        self.tap(190, 190)
        sleep(2000)
        self.tap(500, 200)
        sleep(2000)
        logging.info('storage discharged')
