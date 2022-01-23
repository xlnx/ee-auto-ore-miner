import cv2
import logging
import numpy as np
from contextlib import contextmanager
from util import is_similar, now_sec, ocr, parse_prefix_float, sleep, try_again


CURRENT_SHIP_IND = [
    cv2.imread("current_ship.png"),
    cv2.imread("current_ship_1.png")
]
OVERVIEW_IND = cv2.imread("overview.png")


class Panel():
    def __init__(self) -> None:
        pass

    # ok
    @try_again
    def get_navigate_speed(self) -> float:
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
    def get_storage_percent(self) -> float:
        img = self.screenshot(
            (self.y(40), self.y(130), self.y(118), self.y(155)))
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

    # ok
    def activate(self, row: int, col: int = 0, dt: int = 300) -> None:
        self.tap(
            self.width - self.y(68) - row * self.y(101),
            self.height - self.y(72) - col * self.y(105), dt)
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

    # ok
    def is_docked(self) -> bool:
        y = self.y(290)
        xs = [self.y(_) for _ in [176., 204., 228.]]
        pts = [(x, y) for x in xs]
        img = self.screenshot()
        xs = [img.getpixel((self.width - x, y)) for x, y in pts]
        return all(is_similar(x, (174, 147, 40), 10) for x in xs)

    # ok
    def is_undocked(self) -> bool:
        x = self.width / 2
        img = self.screenshot((x, 0, self.width, self.height))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(
            img, OVERVIEW_IND, cv2.TM_CCOEFF_NORMED)
        dy, dx = np.unravel_index(result.argmax(), result.shape)
        return x - dx < self.y(100) and dy > self.y(450) and dy < self.y(500)

    # ok
    def undock(self) -> None:
        logging.info('undock')
        self.tap(self.width - self.y(108), self.y(300))
        while True:
            if self.is_undocked():
                sleep(4000)
                break
        self.tap(self.width - self.y(64), self.y(506))
        # self.tap(self.width / 2, self.height - 180)
        sleep(2000)
        logging.info('undocked')

    # ok
    @contextmanager
    def open_wirehouse(self) -> None:
        logging.debug('open wirehouse')
        self.tap(10, 10)
        sleep(1000)
        self.tap(self.y(420), self.y(420))
        sleep(3000)
        yield
        self.tap(self.width - self.y(60), self.y(50))
        sleep(3000)

    # ok
    def discharge_storage(self) -> None:
        logging.debug('discharge storage')
        x, y = self.y(15), self.y(100)
        w, h = self.y(315), self.y(700)
        found = False
        while not found:
            img = self.screenshot((x, y, x + w, y + h))
            img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
            for ind in CURRENT_SHIP_IND:
                result = cv2.matchTemplate(img, ind, cv2.TM_CCOEFF_NORMED)
                dy, dx = np.unravel_index(result.argmax(), result.shape)
                logging.info('(%d, %d)', dx, dy)
                if dx <= x and dy + 300 < h:
                    found = True
                    break
            if not found:
                y1, y2 = self.y(200), self.y(100)
                logging.info('need swipe: %d -> %d', y1, y2)
                self.swipe(180, y1, 180, y2, 1000)
        logging.debug('detected current ship: (%d, %d)', x, y)
        x1, y1 = x + dx + self.y(288), y + dy + self.y(100)
        self.tap(x1, y1)
        self.tap(x1, y1)
        found = False
        img = self.screenshot((x, y, x + w, y + h))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        for ind in CURRENT_SHIP_IND:
            result = cv2.matchTemplate(img, ind, cv2.TM_CCOEFF_NORMED)
            dy, dx = np.unravel_index(result.argmax(), result.shape)
            logging.info('(%d, %d)', dx, dy)
            if dx <= x and dy + 300 < h:
                found = True
                break
        assert found
        x, y = x + dx + self.y(288), y + dy + self.y(100)
        self.tap(x - self.y(140), y + self.y(60))
        sleep(2000)
        self.tap(self.width - self.y(370), self.height - self.y(80))
        sleep(2000)
        self.tap(self.y(190), self.y(190))
        sleep(2000)
        self.tap(self.y(500), self.y(200))
        sleep(2000)
        logging.info('storage discharged')
