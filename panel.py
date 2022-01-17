import logging
from util import is_similar, ocr, parse_prefix_float, sleep, try_again
from window import Window


class Panel():
    def __init__(self) -> None:
        pass

    @try_again
    def get_navigate_speed(self) -> float:
        img = self.screenshot(
            (688, self.height - 55, 910, self.height - 29))
        img.save('speed.png')
        speed = ocr(img, numbers=True)
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
        perc = ocr(img, True)
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

    def undock(self) -> None:
        self.tap(self.width - 108, 300)
        sleep(1000 * 20)
        self.tap(self.width - 64, 506)
        sleep(2000)
