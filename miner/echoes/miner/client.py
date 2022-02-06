import logging
from typing import Optional
import cv2
import numpy as np
from .config import config
from .util import sleep, get_static
from ..client import AdbClient

CURRENT_SHIP_IND = [
    cv2.imread(get_static("current_ship.png")),
    cv2.imread(get_static("current_ship_1.png"))
]


class Client(AdbClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, role='Miner')

    # ok
    def warp(self, idx: int) -> None:
        self.overview.target_op(idx, 1, 20)
        for row, col in config.devices.get("balls", []):
            self.activate_device(row, col)
        sleep(5000)
        while True:
            if self.get_navigate_speed() < 20:
                break
        sleep(1000)

    # ok
    def lock(self, idx: int, dt: int = 1000) -> None:
        logging.debug('overview.lock %d', idx)
        self.overview.target_op(idx, 0)
        sleep(dt)

    # ok
    def dock(self, idx: int = 0) -> None:
        self.admin.update('status', 'docking')
        logging.info('overview.dock %d', idx)
        warp_time = int(1000 * config.get('warp_prepare_sec', 10))
        self.overview.open(config.overview.stations, fast=True)
        self.overview.target_op(idx, 1, 20)
        for row, col in config.devices.get("balls", []):
            self.activate_device(row, col, 0)
        sleep(warp_time - 1000)
        for row, col in config.devices.get("stabs", []):
            self.activate_device(row, col, 0)
        sleep(500)
        logging.debug('overview.target_op %d, %d', idx, 0)
        for _ in range(3):
            self.overview.target_op(idx, 0, 20)
            sleep(100)
        while not self.is_docked():
            # logging.info("speed: %d", self.get_navigate_speed())
            # self.get_storage_percent()
            sleep(100)
        logging.info('overview.docked %d', idx)
        self.admin.update('status', 'docked')

    # ok
    def discharge_storage(self) -> None:
        self.admin.update('status', 'discharging')
        logging.debug('open wirehouse')
        self.tap(10, 10)
        sleep(5000)
        self.tap(self.y(420), self.y(420))
        sleep(3000)
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
                y1, y2 = self.y(180), self.y(80)
                logging.info('need swipe: %d -> %d', y1, y2)
                self.swipe(180, y1, 180, y2, 500)
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
        self.tap(self.width - self.y(50), self.y(40))
        sleep(3000)
        self.admin.update('status', 'docked')
        self.admin.update('storage', 0)
