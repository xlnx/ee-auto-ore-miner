import time
import sys
import logging
import traceback
import random
from .counter import StorageCounter
from .client import Client
from .idler import IdleState, Idler
from .laser_miner import LaserMiner
from .local_pirates_idler import LocalPiratesIdler
from .miner import MineState, Miner
from .ore import Ore
from .overview_pirates_idler import OverviewPiratesIdler
from .strip_miner import StripMiner
from .config import config
from .util import sleep


""" constant defs """
TARGET_LIST_REFRESH_DY = 0.5
MAX_LOCK_TARGETS = 5
MAX_MINER_RANGE = 19
# MAX_MINING_HOURS = 12


window = Client(serial=f'{config.adb.host}:{config.adb.port}',
                admin_addr=f'{config.admin.host}:{config.admin.port}',
                user_id=config.get('id', ''))
cnt = StorageCounter(6)

start_time = time.time()
prev_t = 0

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


online = 0


def abort() -> None:
    if not window.is_docked():
        window.dock()
        window.discharge_storage()
    window.admin.disconnect()
    # window.close()
    sys.exit(0)


def try_deploy_mining_task() -> None:
    logging.debug('try deploy mining task')
    while True:
        window.overview.open(config.overview.ores)
        targets = window.overview.list(cand_alphabet=ORE_ALPHABET)
        logging.info('targets: %s', targets)
        ores = [(d, Ore.from_text(t)) for d, t in targets]
        logging.info('found ores: %s', ores)
        if len(ores) == 0 or all(_[1] == Ore.Unknown for _ in ores):
            return False
        state = miner.apply(ores)
        if state == MineState.Success:
            window.admin.update('status', 'mining')
            return True
        elif state == MineState.Fail:
            return False
        elif state == MineState.Retry:
            continue
        else:
            raise NotImplementedError()


def deploy_mining_task(check: bool = True) -> None:
    window.admin.update('status', 'deploying')
    if check:
        if try_deploy_mining_task():
            return True
        logging.warn('deploy failed, seeking asteroid belts')
    window.overview.open(config.overview.asteroid_belts)
    asteroid_belts = window.overview.list()
    logging.info('asteroid belts: %s', asteroid_belts)
    n = len(asteroid_belts)
    if n > 1:
        idx = random.randint(1, n - 1)
        window.warp(idx)
    return try_deploy_mining_task()


def apply_task(docked: bool, name: str, *args) -> bool:
    logging.info('apply task: %s', name)
    global online
    if name == 'offline' and online:
        if not docked:
            window.dock()
            window.discharge_storage()
        online = 0
        window.admin.update('online', online)
        return False
    if name == 'online' and not online:
        assert docked
        online = 1
        window.admin.update('online', online)
    return True


def main_loop(need_check: bool = True) -> None:
    t = time.time() - start_time
    if t / 3600 >= config.max_time_hr:
        abort()
    if need_check:
        window.admin.heartbeat()
        while len(window.admin.tasks):
            name, args = window.admin.tasks.pop()
            if not apply_task(False, name, *args):
                return
        logging.debug("miner.idle()")
        state = miner.idle(docked=False)
        if state == IdleState.Deploy:
            need_check = False
        elif state == IdleState.Nothing:
            pass
    global prev_t
    dt = t - prev_t
    value = 0
    if dt >= 10:
        prev_t = t
        value = window.get_storage_percent()
        window.admin.update('storage', value)
        logging.info("storage reached %s%%", value)
        if need_check:
            if value < 95 and cnt.add_and_test(value):
                window.admin.update('status', 'mining')
                return
            logging.info(
                "ore mining task stopped with storage = %f%%", value)
    elif need_check:
        return

    if value > 90:
        logging.info("storage nearly full, deploy docking task")
        window.dock()
        window.discharge_storage()
        logging.debug("miner.idle()")
        miner.idle(docked=True)
        window.undock()
        need_check = False
    logging.info("deploy mining task")
    for _ in range(5):
        if deploy_mining_task(need_check):
            break
        # change_aspect()
    else:
        logging.warn("failed to deploy mining task, exit now")
        abort()
    cnt.clear()


def main():
    try:
        window.local.calibrate()
        system = window.get_system_name()
        window.admin.update('system', system)
        logging.info("init success: %s", system)
        global online
        online = 1
        window.admin.update('online', online)
        init = True
        while True:
            if online:
                need_check = True
                if init:
                    value = window.get_storage_percent()
                    window.admin.update('storage', value)
                    if window.is_docked():
                        window.admin.update('status', 'docked')
                        window.undock()
                        need_check = False
                    else:
                        window.admin.update('status', 'undocked')
                    init = False
                main_loop(need_check)
            else:
                window.admin.heartbeat()
                while len(window.admin.tasks):
                    name, args = window.admin.tasks.pop()
                    apply_task(True, name, *args)
                init = True
            sleep(500)
    except Exception:
        print(traceback.format_exc())
        abort()
