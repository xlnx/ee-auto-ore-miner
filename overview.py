from config import config
from typing import List, Optional, Tuple
import logging
from util import ocr, parse_prefix_float, sleep, try_again


ITEM_HEIGHT = 86


class Overview():
    def __init__(self) -> None:
        self._curr = -1

    def open(self, idx: int) -> None:
        if self._curr != idx:
            logging.debug('overview.open %d', idx)
            self.tap(1300, 30)
            self.tap(1300, 160 + (ITEM_HEIGHT + 2) * idx)
            sleep(1000)
            self._curr = idx

    @try_again
    def list(self, max_items: int = 5, cand_alphabet: Optional[str] = None) -> List[Tuple[float, str]]:
        logging.debug('overview.list %d', max_items)
        img = self.screenshot((1211, 67, 1522, 537))
        li = []
        for i in range(0, max_items):
            di = img.crop((36, ITEM_HEIGHT * i,
                           105, ITEM_HEIGHT * i + 52))
            di = ocr(di, cand_alphabet="0123456789.", single_line=True)
            ui = img.crop((36, ITEM_HEIGHT * i + 50,
                           105, ITEM_HEIGHT * (i + 1)))
            ui = ocr(ui, cand_alphabet="千米天文单位", single_line=True)
            ti = img.crop((108, ITEM_HEIGHT * i,
                           300, ITEM_HEIGHT * (i + 1)))
            ti = ocr(ti, cand_alphabet=cand_alphabet)
            if ti == '' and di == '':
                break
            # unit = DistanceUnit.Unknown
            unit = 149597870.7
            if '千' in ui or '米' in ui:
                unit = 1
            di = parse_prefix_float(di)
            li.append((di * unit, ti))
        logging.debug('overview.list %s', li)
        return li

    @try_again
    def list_fast(self, max_items: int = 1, cand_alphabet: Optional[str] = None) -> List[str]:
        logging.debug('overview.list_fast %d', max_items)
        img = self.screenshot((1211, 67, 1522, 537))
        li = []
        for i in range(0, max_items):
            ti = img.crop((108, ITEM_HEIGHT * i,
                           300, ITEM_HEIGHT * (i + 1)))
            ti = ocr(ti, cand_alphabet=cand_alphabet)
            if ti == '':
                break
            li.append(ti)
        logging.debug('overview.list_fast %s', li)
        return li

    def target_op(self, idx: int, op_idx: int, dt: int = 300) -> None:
        logging.debug('overview.target_op %d, %d', idx, op_idx)
        y = 67 + ITEM_HEIGHT * idx
        self.tap(1300, y + 50)
        self.tap(1000, y + 95 * op_idx + 50, dt)

    def warp(self, idx: int) -> None:
        self.target_op(idx, 1, 20)
        for row, col in config.devices.get("balls", []):
            self.activate(row, col)
        sleep(5000)
        while True:
            if self.get_navigate_speed() < 20:
                break
        sleep(1000)

    def lock(self, idx: int, dt: int = 1000) -> None:
        logging.debug('overview.lock %d', idx)
        self.target_op(idx, 0)
        sleep(dt)

    def dock(self, idx: int = 0) -> None:
        logging.info('overview.dock %d', idx)
        self.open(config.overview.stations)
        self.target_op(idx, 0, 20)
        for row, col in config.devices.get("balls", []):
            self.activate(row, col)
        for row, col in config.devices.get("stabs", []):
            self.activate(row, col)
        while not self.is_docked():
            sleep(300)
        logging.info('overview.docked %d', idx)

    def fast_dock(self, idx: int = 0) -> None:
        logging.info('overview.fast_dock %d', idx)
        s_idx = config.overview.stations
        if self._curr != s_idx:
            logging.debug('overview.open %d', s_idx)
            self.tap(1300, 30, 0)
            self.tap(1300, 160 + (ITEM_HEIGHT + 2) * s_idx, 0)
            self._curr = s_idx
        y = 67 + ITEM_HEIGHT * idx
        self.tap(1300, y + 50, 0)
        self.tap(1000, y + 95 * 1 + 50, 0)
        for row, col in config.devices.get("balls", []):
            self.tap(
                self.width - 68 - row * 101,
                self.height - 72 - col * 105, 0)
        for row, col in config.devices.get("stabs", []):
            self.tap(
                self.width - 68 - row * 101,
                self.height - 72 - col * 105, 0)
        logging.debug('overview.target_op %d, %d', idx, 0)
        y = 67 + ITEM_HEIGHT * idx
        self.tap(1300, y + 50, 0)
        self.tap(1000, y + 95 * 0 + 50, 0)
        while not self.is_docked():
            sleep(300)
        logging.info('overview.fast_docked %d', idx)
