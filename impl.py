import os
import sys
import logging
from contextlib import contextmanager
from utils import *
from typing import *
from ore import Ore


""" constant defs """
TARGET_LIST_REFRESH_DY = 0.5
MAX_LOCK_TARGETS = 5
MAX_MINER_RANGE = 18


""" window property defs """
GAME_RECT = get_window_rect("BlueStacks")
x1, y1, x2, y2 = GAME_RECT
t, r = 42, 62
x2 -= r
y1 += t
GAME_RECT = (x1, y1, x2, y2)
wnd = Window(GAME_RECT)


w1, w2, w3 = 0.224, 0.177, 0.047
h1, h2 = 0.078, 0.1736


###  DATA  ###
def change_aspect() -> None:
    dy = (random.random() - 0.5) * 0.01
    wnd.drag_ease(0.35, 0.01 + dy, 0.45, 0.01 - dy)


def change_aspect_while_fail(func):
    def inner(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except:
                change_aspect()
    return inner


@change_aspect_while_fail
def get_storage_percent() -> float:
    g = wnd.screenshot()[
        0.029:0.070,
        0.145:0.173,
        :
    ]
    g = g.map(lambda img: img * 2)
    g.save('storage.jpg')
    perc = g.ocr(numbers=True)

    if perc[-1] != '%':
        raise NotImplementedError()
    return parse_prefix_float(perc)


###  OVERVIEW  ###
def get_overview_target_list(
    from_idx: int,
    to_idx: int
) -> List[Tuple[int, str]]:

    g = wnd.screenshot()
    g.save('g.jpg')
    r = []
    hi = h2 - h1
    for i in range(from_idx, to_idx):
        try:
            gi = g[
                -w2:-w3,
                h1+hi*i:h1+hi*(i+1),
                :
            ]
            # gi.save('{}.jpg'.format(i))
            name = gi.ocr()
            gi = g[
                -w1+(w1-w2)*0.4:-w2,
                h1+hi*(i+0.28):h1+hi*(i+0.55),
                :
            ]
            # gi.save('{}.jpg'.format(i))
            di = parse_prefix_int_or(gi.ocr(numbers=True), None)
            r.append((di, name))
        except:
            break
    if len(r) == 0:
        return r
    d, o = r[-1]
    if d is None:
        r[-1] = 9999, o
    for i in range(len(r))[:-1][::-1]:
        d, o = r[i]
        if d is None:
            r[i] = r[i+1][0], o
    return r


def wnd_filter_target_list(
    filter_idx: int,
    target_count: int = 9,
    need_stop: bool = True
) -> List[Tuple[int, str]]:

    # def wnd_refresh():
    #     wnd.drag_ease(-w2, h2, -w2, h2 + TARGET_LIST_REFRESH_DY)
    #     wnd.move_to(0, 0)

    # apply overview filter
    wnd.click(-0.18, 0.04)
    sleep(1)
    h1, dh = 0.181, 0.0987
    wnd.click(-0.138, h1 + filter_idx * dh)
    sleep(1)
    if need_stop:
        wnd_stop_navigate()
    # for _ in range(3):
    #     wnd_refresh()
    if need_stop:
        # wait_until_engine_stop(wnd_refresh)
        wait_until_engine_stop(lambda: sleep(1))
    # wait for ui bounce
    # sleep(0.5)
    return get_overview_target_list(0, target_count)


###  TARGETS  ###
def wnd_lock_target(target_idx: int) -> None:
    _wnd_target_operation(target_idx, 0, wnd.click)


def wnd_unlock_all_targets() -> None:
    for i in range(MAX_LOCK_TARGETS)[::-1]:
        y = 0.07
        x1, x2 = 0.30, 0.36
        x = x1 + i * (x2 - x1)
        wnd.drag_ease(-x, y, -x, 0.4)


def wnd_approach_target(target_idx: int, dist: Optional[float] = None) -> None:
    if dist is None:
        fn = wnd.click
    else:
        def fn(x, y): return _wnd_select_distance(x, y, dist)
    _wnd_target_operation(target_idx, 1, fn)


def wnd_orbit_target(target_idx: int, dist: Optional[float] = None) -> None:
    if dist is None:
        fn = wnd.click
    else:
        def fn(x, y): return _wnd_select_distance(x, y, dist)
    _wnd_target_operation(target_idx, 2, fn)


def _wnd_target_operation(
    target_idx: int,
    op_idx: int,
    cb: Callable[[float, float], None]
) -> None:
    hi = h2 - h1
    ht = h1+hi*(target_idx+0.5)
    wnd.drag_ease(-w2, h2, -w2, h2+0.05)
    sleep(1)
    wnd.click(-w2, ht)
    sleep(1)
    x, y = -0.36, ht+op_idx*0.1044
    x %= 1
    y %= 1
    cb(x, y)
    sleep(0.5)


def _wnd_select_distance(x1: float, y1: float, dist: float) -> None:
    def ease(x):
        if x < 0.5:
            return x * 2
        return 1
    rx, ry = -0.360, 0.4197
    x2, y2 = rx, min(max(ry, y1), 1-ry)
    min_x, max_x = 0.07, 0.216
    dx = (max_x - min_x) / 100.0
    x2 += (min_x + dx * dist) * 1.08
    wnd.drag_ease(x1, y1, x2, y2, dur=1.5, ease=ease)


###  NAVIGATING  ###
@change_aspect_while_fail
def get_navigate_speed() -> float:
    speed = wnd.screenshot()[
        0.40:0.60,
        0.935:0.97,
        :
    ]
    speed.save('speed.jpg')
    speed = speed.ocr(numbers=True)
    unit = 1
    if '天文单位' in speed:
        unit = 149597870700.0
    elif '千米' in speed:
        unit = 1000.0
    elif '米' in speed:
        unit = 1.0
    else:
        raise NotImplementedError()
    speed = parse_prefix_float(speed) * unit
    logging.info('current speed is %s m/s', speed)
    return speed


def wait_until_engine_stop(idle) -> None:
    sleep(1)
    while get_navigate_speed() != 0:
        idle()
        sleep(3)


def wnd_stop_navigate() -> None:
    wnd.click(0.5, 0.5)
    sleep(1)
    wnd.click(0.5, 0.5)
    sleep(1)


def wnd_dock(target_idx) -> None:
    targets = wnd_filter_target_list(2)
    d, s = targets[target_idx]
    logging.info('docking %s', s)
    if d != 0:
        _wnd_target_operation(target_idx, 0, wnd.click)
    else:
        _wnd_target_operation(target_idx, 1, wnd.click)
    pts = [
        (0.11208642808912897, 0.31850961538461536),
        (0.13031735313977041, 0.31850961538461536),
        (0.14652261985145174, 0.31850961538461536),
    ]
    docked = False
    while not docked:
        g = wnd.screenshot()
        xs = [g[-x, y, :].data for x, y in pts]
        docked = all(
            145 < r < 215 and 120 < g < 180 and 10 < b < 70
            for r, g, b in xs
        )
        sleep(3)


def wnd_undock() -> None:
    logging.info('undocking')
    wnd.click(-0.0946, 0.341)
    sleep(30)
    wnd.click(-0.0378, 0.557)
    sleep(2)


def wnd_warp_to_signal(target_idx: int, dist: Optional[float] = None) -> None:
    if dist is None:
        fn = wnd.click
    else:
        def fn(x, y): return _wnd_select_distance(x, y, dist)
    _wnd_target_operation(target_idx, 1, fn)
    sleep(10)
    wait_until_engine_stop(lambda: None)


###  DEVICES  ###
def wnd_activate_device(row: int, col: int) -> None:
    wi, hi = 0.04470, 0.08287
    w, h = wi*(2*col+1), hi*(2*row+1)
    wnd.click(-w, -h)
    sleep(1)


###  SPACE STATION  ##
@contextmanager
def wnd_open_wirehouse() -> None:
    wnd.click(0.045, 0.156)
    sleep(3)
    yield
    wnd.click(-0.038, 0.059)
    sleep(3)


def wnd_discharge_storage() -> None:
    wnd.click(0.110, 0.764)
    sleep(2)
    wnd.click(-0.233, -0.095)
    sleep(2)
    wnd.click(0.112, 0.205)
    sleep(2)
    wnd.click(0.355, 0.234)
    sleep(2)
    logging.info('storage discharged')


def get_opt_ore_targets(ores) -> List[Tuple[int, Ore]]:
    ores = [
        (i, d, o)
        for i, (d, o)
        in enumerate(ores)
    ]
    ores = [
        (i, d, o)
        for i, d, o in ores
        if o != Ore.Unknown and d <= MAX_MINER_RANGE
    ]
    ores = sorted(
        ores,
        key=lambda x: x[2].market_price_per_volume,
        reverse=True
    )
    targets = [i for i, _, _ in ores[:MAX_LOCK_TARGETS]]
    return targets

###  LOGICAL  ###


def wnd_try_deploy_mining_task() -> None:
    while True:
        targets = wnd_filter_target_list(0)
        ores = [(d, Ore.from_text(t)) for d, t in targets]
        logging.info('found ores: %s', ores)
        if len(ores) == 0 or ores[0][1] == Ore.Unknown:
            return False
        targets = get_opt_ore_targets(ores)
        logging.info('optimal targets: %s', [ores[i] for i in targets])
        if len(targets) > 0:
            wnd_unlock_all_targets()
            for idx in targets:
                wnd_lock_target(idx)
            sleep(5)
            wnd_activate_device(0, 0)
            wnd_activate_device(0, 1)
            wnd_orbit_target(targets[0], 2)
            return True
        wnd_orbit_target(0, 2)
        di = 9999
        while di > 8:
            targets = get_overview_target_list(0, 1)
            if len(targets) == 0:
                break
            di, _ = targets[0]
            logging.info('d = %f km', di)
            sleep(1)


def wnd_deploy_mining_tasks() -> None:
    if wnd_try_deploy_mining_task():
        return True
    logging.warn('')
    asteroid_belts = wnd_filter_target_list(1, need_stop=False)
    n = len(asteroid_belts)
    if n > 1:
        idx = random.randint(1, n - 1)
        wnd_warp_to_signal(idx)
    return wnd_try_deploy_mining_task()


class StorageCounter():

    def __init__(self, max_tick) -> None:
        self._arr = []
        self._max_tick = max_tick

    def add_and_test(self, value) -> bool:
        if len(self._arr) < self._max_tick:
            self._arr.append(value)
        elif len(self._arr) == self._max_tick:
            self._arr = self._arr[1:] + [value]
            return any(value != _ for _ in self._arr)
        else:
            raise NotImplementedError()
        return True

    def get(self):
        if len(self._arr) == 0:
            return None
        return self._arr[-1]

    def clear(self):
        self._arr = []


cnt = StorageCounter(3)


def wnd_main_loop() -> None:
    value = get_storage_percent()
    logging.info("storage reached %s%%", value)
    if value < 95 and cnt.add_and_test(value):
        return
    logging.info(
        "ore mining task stopped with storage = %f%%", value)
    if value > 90:
        logging.info("storage nearly full, deploy docking task")
        targets = wnd_filter_target_list(2, need_stop=False)
        if len(targets) == 0:
            raise NotImplementedError()
        wnd_dock(0)
        with wnd_open_wirehouse():
            wnd_discharge_storage()
        wnd_undock()
        for _ in range(99):
            cnt.add_and_test(0)
    else:
        logging.info("deploy mining task")
        if not wnd_deploy_mining_tasks():
            logging.warn("failed to deploy mining task, exit now")
            sys.exit(0)
        cnt.clear()


def main():
    file_handler = logging.FileHandler(filename='tmp.log')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(
        level=logging.DEBUG,
        format=u'[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )

    while True:
        wnd_main_loop()
        sleep(30)
