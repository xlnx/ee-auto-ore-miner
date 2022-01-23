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
from util import now_sec, sleep
import sys
import logging
import random


file_handler = logging.FileHandler(filename='tmp.log', encoding='utf-8')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers,
    force=True
)


""" constant defs """
TARGET_LIST_REFRESH_DY = 0.5
MAX_LOCK_TARGETS = 5
MAX_MINER_RANGE = 19
# MAX_MINING_HOURS = 12


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

ORE_ALPHABET = "".join(set("".join([
    "凡晶石",
    "灼烧岩",
    "干焦岩",
    "斜长岩",
    "奥贝尔石",
    "水硼砂",
    "杰斯贝矿",
    "希莫非特",
    "同位原矿",
    "灰岩",
    "黑赭石",
    "片麻岩",
    "克洛基石",
    "双多特石",
    "艾克诺岩",
    "基腹断岩",
    "小行星富[]"
])))


def abort() -> None:
    window.dock()
    with window.open_wirehouse():
        window.discharge_storage()
    # window.close()
    sys.exit(0)


def try_deploy_mining_task() -> None:
    logging.debug('try deploy mining task')
    while True:
        window.open(config.overview.ores)
        targets = window.list(cand_alphabet=ORE_ALPHABET)
        logging.info('targets: %s', targets)
        ores = [(d, Ore.from_text(t)) for d, t in targets]
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
    if t / 3600 >= config.max_time_hr:
        abort()
    if need_check:
        logging.debug("miner.idle()")
        if miner.idle():
            need_check = False
    global prev_t
    dt = t - prev_t
    value = 0
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
    elif need_check:
        return

    if value > 90:
        logging.info("storage nearly full, deploy docking task")
        window.dock()
        with window.open_wirehouse():
            window.discharge_storage()
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
    logging.info("init success")
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
