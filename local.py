import logging
from typing import Tuple
import cv2
import numpy as np
from util import ocr

LOCAL_IND = [
    cv2.imread("rivals.png"),
    cv2.imread("criminals.png"),
    cv2.imread("neutral.png"),
]


class Local():
    def __init__(self) -> None:
        self._open = False
        self.calibrate_local()

    def calibrate_local(self):
        logging.info('calibrate locals')
        while True:
            img = self.screenshot()
            img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
            xs, ys = [], []
            for ind in LOCAL_IND:
                result = cv2.matchTemplate(
                    img, ind, cv2.TM_CCOEFF_NORMED)
                dy, dx = np.unravel_index(result.argmax(), result.shape)
                xs.append(dx)
                ys.append(dy)
            if max(ys) - min(ys) <= 3:
                logging.info('calibrate pos: %s, %s', xs, ys[0])
                self._local_xs = xs
                self._local_y = min(ys)
                self._open = True
                break
            else:
                logging.info('recalibrate')
                self.tap(self.y(50), self.y(735))

    def open_local(self) -> None:
        logging.debug('open locals')
        if not self._open:
            self.tap(self.y(50), self.y(735))
            self._open = True

    def close_local(self) -> None:
        logging.debug('close locals')
        if self._open:
            self.tap(self.y(50), self.y(735))
            self._open = False

    def toggle_local(self) -> None:
        logging.debug('toggle locals')
        if self._open:
            self.close_local()
        else:
            self.open_local()

    def get_local_count(self) -> Tuple[int, int, int]:
        logging.debug('toggle locals')
        dx = self.y(50)
        dy = self.y(24)
        xs = [_ + dy for _ in self._local_xs]
        y = self._local_y
        img = self.screenshot()
        ns = []
        for x in xs:
            i = img.crop((x, y, x + dx, y + dy))
            n = ocr(i, cand_alphabet='0123456789', single_line=True)
            if n != '':
                n = int(n)
            else:
                n = 0
            ns.append(n)
        x = self.y(50)
        y = self.y(728)
        i = img.crop((x, y, x + dx, y + dy))
        n = ocr(i, cand_alphabet='0123456789', single_line=True)
        if n != '':
            n = int(n)
        else:
            n = 0
        ns = [ns[0] + ns[1], ns[2], n]
        logging.debug('locals: %s', ns)
        return tuple(ns)
