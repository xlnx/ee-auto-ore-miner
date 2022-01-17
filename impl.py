from counter import StorageCounter
from game_window import GameWindow
from idler import Idler
from laser_miner import LaserMiner
from local_pirates_idler import LocalPiratesIdler
from miner import MineState, Miner
from ore import Ore
from overview_pirates_idler import OverviewPiratesIdler
from strip_miner import StripMiner
from config import config
from util import now_sec, ocr, sleep, parse_prefix_float
from contextlib import contextmanager
import sys
import cv2
import numpy as np
import logging
import random
from typing import List


""" constant defs """
TARGET_LIST_REFRESH_DY = 0.5
MAX_LOCK_TARGETS = 5
MAX_MINER_RANGE = 19
MAX_MINING_HOURS = 12

CURRENT_SHIP_IND = cv2.imread("current_ship.png")


window = GameWindow()
cnt = StorageCounter(6)

start_time = now_sec()

idler: Idler
if config.idler.type == "overview":
    idler = OverviewPiratesIdler()
elif config.idler.type == "local":
    idler = LocalPiratesIdler()
else:
    raise NotImplementedError()

miner: Miner
if config.devices.type == "laser":
    miner = LaserMiner(window, idler)
elif config.devices.type == "strip":
    miner = StripMiner(window, idler)
else:
    raise NotImplementedError()


@contextmanager
def open_wirehouse() -> None:
    logging.debug('open wirehouse')
    window.tap(10, 10)
    sleep(1000)
    window.tap(420, 420)
    sleep(3000)
    yield
    window.tap(window.width - 60, 50)
    sleep(3000)


def discharge_storage() -> None:
    logging.debug('discharge storage')
    x, y = 15, 100
    w, h = 315, 700
    while True:
        img = window.screenshot((x, y, x + w, y + h))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(
            img, CURRENT_SHIP_IND, cv2.TM_CCOEFF_NORMED)
        dy, dx = np.unravel_index(result.argmax(), result.shape)
        logging.info('(%d, %d)', dx, dy)
        if dy + 300 < h:
            break
        logging.debug('need swipe')
        window.swipe(180, 500, 180, 400, 1000)
        sleep(2000)
    logging.debug('detected current ship: (%d, %d)', x, y)
    x, y = x + dx + 288, y + dy + 100
    window.tap(x, y)
    window.tap(x, y)
    window.tap(x - 140, y + 60)
    sleep(2000)
    window.tap(window.width - 370, window.height - 80)
    sleep(2000)
    window.tap(190, 190)
    sleep(2000)
    window.tap(500, 200)
    sleep(2000)
    logging.info('storage discharged')


def abort() -> None:
    window.dock()
    with open_wirehouse():
        discharge_storage()
    # window.close()
    sys.exit(0)


def try_deploy_mining_task() -> None:
    logging.debug('try deploy mining task')
    while True:
        window.open(config.overview.ores)
        targets = window.list()
        logging.debug('targets: %s', targets)
        ores = [(item.distance, Ore.from_text(item.label)) for item in targets]
        logging.info('found ores: %s', ores)
        if len(ores) == 0 or all(_[1] == Ore.Unknown for _ in ores):
            return False
        state = miner.apply(ores)
        if state == MineState.Success:
            return True
        elif state == MineState.Fail:
            return False
        elif state == MineState.Retry:
            continue
        else:
            raise NotImplementedError()


def deploy_mining_task(check: bool = True) -> None:
    if check:
        if try_deploy_mining_task():
            return True
        logging.warn('deploy failed, seeking asteroid belts')
    window.open(config.overview.asteroid_belts)
    asteroid_belts = window.list()
    logging.info('asteroid belts: %s', asteroid_belts)
    n = len(asteroid_belts)
    if n > 1:
        idx = random.randint(1, n - 1)
        window.warp(idx)
    return try_deploy_mining_task()


prev_t = 0


def main_loop(need_check: bool = True) -> None:
    t = now_sec() - start_time
    if t / 3600 >= MAX_MINING_HOURS:
        abort()
    if need_check:
        logging.debug("miner.idle()")
        miner.idle()
    global prev_t
    dt = t - prev_t
    if dt >= 10:
        prev_t = t
        value = window.get_storage_percent()
        logging.info("storage reached %s%%", value)
        if need_check:
            if value < 95 and cnt.add_and_test(value):
                # window.open(config.overview.ores)
                return
            logging.info(
                "ore mining task stopped with storage = %f%%", value)
    else:
        return

    if value > 90:
        logging.info("storage nearly full, deploy docking task")
        window.dock()
        with open_wirehouse():
            discharge_storage()
        window.undock()
        need_check = False
    logging.info("deploy mining task")
    for _ in range(3):
        if deploy_mining_task(need_check):
            break
        # change_aspect()
    else:
        logging.warn("failed to deploy mining task, exit now")
        abort()
    cnt.clear()


def main():
    file_handler = logging.FileHandler(filename='tmp.log', encoding='utf-8')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(
        level=logging.INFO,
        format=u'[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )

    print("init success")
    try:
        need_check = True
        if window.is_docked():
            window.undock()
            need_check = False
        while True:
            main_loop(need_check)
            need_check = True
    except Exception as e:
        print(e)
        abort()
    # discharge_storage()
