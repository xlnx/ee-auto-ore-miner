from config import config
from typing import List
import logging
from panel import Panel
from util import is_similar, ocr, parse_prefix_float, sleep, try_again
from window import Window
from enum import Enum


class DistanceUnit(Enum):
    KM = 1
    AU = 2
    Unknown = 4

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        if self == DistanceUnit.KM:
            return 'KM'
        elif self == DistanceUnit.AU:
            return 'AU'
        return '??'


class OverviewItem:
    def __init__(self, d: float, u: DistanceUnit, t: str) -> None:
        self._d = d
        self._u = u
        self._t = t

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'{self._d}({self._u}):{self._t}'

    @property
    def distance(self) -> float:
        return self._d

    @property
    def label(self) -> str:
        return self._t


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
    def list(self, max_items: int = 5) -> List[OverviewItem]:
        logging.debug('overview.list %d', max_items)
        img = self.screenshot((1211, 67, 1522, 537))
        li = []
        for i in range(0, max_items):
            di = img.crop((36, ITEM_HEIGHT * i,
                           105, ITEM_HEIGHT * i + 52))
            di = ocr(di, numbers=True)
            ui = img.crop((36, ITEM_HEIGHT * i + 50,
                           105, ITEM_HEIGHT * (i + 1)))
            ui = ocr(ui)
            ti = img.crop((108, ITEM_HEIGHT * i,
                           300, ITEM_HEIGHT * (i + 1)))
            ti = ocr(ti)
            if ti == '' and di == '':
                break
            unit = DistanceUnit.Unknown
            if '天文' in ui:
                unit = DistanceUnit.AU
            elif '千' in ui:
                unit = DistanceUnit.KM
            di = parse_prefix_float(di)
            li.append(OverviewItem(di, unit, ti))
        logging.debug('overview.list %s', li)
        return li

    @try_again
    def list_fast(self, max_items: int = 1) -> List[str]:
        logging.debug('overview.list_fast %d', max_items)
        img = self.screenshot((1211, 67, 1522, 537))
        li = []
        for i in range(0, max_items):
            ti = img.crop((108, ITEM_HEIGHT * i,
                           300, ITEM_HEIGHT * (i + 1)))
            ti = ocr(ti)
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
            if self.get_navigate_speed() == 0:
                break
        sleep(1000)

    def approach(self, idx: int) -> None:
        self.target_op(idx, 1)
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
        for row, col in config.devices.get("balls", []):
            self.tap(
                self.width - 68 - row * 101,
                self.height - 72 - col * 105, 0)
        for row, col in config.devices.get("stabs", []):
            self.tap(
                self.width - 68 - row * 101,
                self.height - 72 - col * 105, 0)
        s_idx = config.overview.stations
        if self._curr != s_idx:
            logging.debug('overview.open %d', s_idx)
            self.tap(1300, 30, 0)
            self.tap(1300, 160 + (ITEM_HEIGHT + 2) * s_idx, 0)
            self._curr = s_idx
        logging.debug('overview.target_op %d, %d', idx, 0)
        y = 67 + ITEM_HEIGHT * idx
        self.tap(1300, y + 50, 0)
        self.tap(1000, y + 95 * 0 + 50, 0)
        while not self.is_docked():
            sleep(300)
        logging.info('overview.fast_docked %d', idx)
