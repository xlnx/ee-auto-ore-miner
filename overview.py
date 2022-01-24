from config import config
from typing import List, Optional, Tuple
import logging
from util import ocr, parse_prefix_float, sleep, try_again


ITEM_HEIGHT = 86


class Overview():
    def __init__(self) -> None:
        self._curr = -1

    @property
    def item_height(self) -> int:
        return self.y(86)

    # ok
    def open(self, idx: int, fast: bool = False) -> None:
        if self._curr != idx:
            logging.debug('overview.open %d', idx)
            x = self.width - self.y(300)
            self.tap(x, self.y(30))
            self.tap(x, self.y(160) + self.item_height * idx)
            if not fast:
                sleep(1000)
            self._curr = idx

    # ok
    @try_again
    def list(self, max_items: int = 5, cand_alphabet: Optional[str] = None) -> List[Tuple[float, str]]:
        logging.debug('overview.list %d', max_items)
        x1 = self.width - self.y(389)
        x2 = self.width - self.y(78)
        y1 = self.y(67)
        y2 = self.y(537)
        img = self.screenshot((x1, y1, x2, y2))
        li = []
        for i in range(0, max_items):
            di = img.crop((self.y(36), self.item_height * i,
                           self.y(105), self.item_height * i + 52))
            di = ocr(di, cand_alphabet="0123456789.", single_line=True)
            ui = img.crop((self.y(36), self.item_height * i + 50,
                           self.y(105), self.item_height * (i + 1)))
            ui = ocr(ui, cand_alphabet="千米天文单位", single_line=True)
            ti = img.crop((self.y(108), self.item_height * i,
                           self.y(300), self.item_height * (i + 1)))
            ti = ocr(ti, cand_alphabet=cand_alphabet)
            if ti == '' and di == '':
                break
            # unit = DistanceUnit.Unknown
            try:
                di = parse_prefix_float(di)
                unit = 149597870.7
                if '千' in ui or '米' in ui:
                    unit = 1
                di = di * unit
            except Exception:
                di = float('inf')
            li.append((di, ti))
        logging.debug('overview.list %s', li)
        return li

    # ok
    @try_again
    def list_fast(self, max_items: int = 1, cand_alphabet: Optional[str] = None) -> List[str]:
        logging.debug('overview.list_fast %d', max_items)
        x1 = self.width - self.y(389)
        x2 = self.width - self.y(78)
        y1 = self.y(67)
        y2 = self.y(537)
        img = self.screenshot((x1, y1, x2, y2))
        li = []
        for i in range(0, max_items):
            ti = img.crop((self.y(108), self.item_height * i,
                           self.y(300), self.item_height * (i + 1)))
            ti = ocr(ti, cand_alphabet=cand_alphabet)
            if ti == '':
                break
            li.append(ti)
        logging.debug('overview.list_fast %s', li)
        return li

    # ok
    def target_op(self, idx: int, op_idx: int, dt: int = 300) -> None:
        logging.debug('overview.target_op %d, %d', idx, op_idx)
        y = self.y(67) + self.item_height * idx
        self.tap(self.width - self.y(300), y + self.y(50))
        self.tap(self.width - self.y(600), y +
                 self.y(95) * op_idx + self.y(50), dt)

    # ok
    def warp(self, idx: int) -> None:
        self.target_op(idx, 1, 20)
        for row, col in config.devices.get("balls", []):
            self.activate(row, col)
        sleep(5000)
        while True:
            if self.get_navigate_speed() < 20:
                break
        sleep(1000)

    # ok
    def lock(self, idx: int, dt: int = 1000) -> None:
        logging.debug('overview.lock %d', idx)
        self.target_op(idx, 0)
        sleep(dt)

    # ok
    def dock(self, idx: int = 0) -> None:
        self.admin.emit('update_status', 'docking')
        logging.info('overview.dock %d', idx)
        warp_time = int(1000 * config.get('warp_prepare_sec', 10))
        self.open(config.overview.stations, fast=True)
        self.target_op(idx, 1, 20)
        for row, col in config.devices.get("balls", []):
            self.activate(row, col, 0)
        sleep(warp_time - 1000)
        for row, col in config.devices.get("stabs", []):
            self.activate(row, col, 0)
        sleep(1000)
        logging.debug('overview.target_op %d, %d', idx, 0)
        for _ in range(3):
            self.target_op(idx, 0, 20)
            sleep(100)
        while not self.is_docked():
            # logging.info("speed: %d", self.get_navigate_speed())
            # self.get_storage_percent()
            sleep(100)
        logging.info('overview.docked %d', idx)
        self.admin.emit('update_status', 'docked')
