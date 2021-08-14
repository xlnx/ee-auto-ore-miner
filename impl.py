# import mss
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

# W, H = X2 - X1, Y2 - Y1


# def ix(x):
#     return int(W * x)

# def iy(y):
#     return int(H * y)


w1, w2, w3 = 0.224, 0.177, 0.047
h1, h2 = 0.078, 0.1736


def wnd_navigate_stop() -> None:
    wnd.click(0.5, 0.5)
    sleep(1)
    wnd.click(0.5, 0.5)
    sleep(1)


def wnd_change_view() -> None:
    wnd.drag_ease(0.45, 0.01, 0.55, 0.04)


def change_aspect_while_fail(func):
    def inner(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except:
                wnd_change_view()
    return inner


@change_aspect_while_fail
def get_navigate_speed() -> float:
    speed = wnd.screenshot()[
        0.45:0.55,
        0.935:0.97,
        :
    ]
    speed.save('speed.jpg')
    speed = speed.ocr(numbers=True)
    unit = 1
    if '米/秒' in speed:
        unit = 1
    return parse_prefix_float(speed) * unit


def wnd_apply_overview_filter(idx: int) -> None:
    # apply overview filter
    wnd.click(-0.18, 0.04)
    sleep(1)
    wnd.click(-0.138, 0.16)
    sleep(1)


def wnd_refresh_target_list(
    overview_type: int, 
    target_count: int = 9,
    need_stop: bool = True
) -> List[Tuple[int, str]]:

    def wnd_refresh():
        wnd.drag_ease(-w2, h2, -w2, h2 + TARGET_LIST_REFRESH_DY)
        wnd.move_to(0, 0)

    wnd_apply_overview_filter(overview_type)
    if need_stop:
        wnd_navigate_stop()
        for _ in range(4):
            wnd_refresh() 
        while get_navigate_speed() != 0:
            wnd_refresh()
    else:
        wnd_refresh()
    # wait for ui bounce
    sleep(0.5)
    g = wnd.screenshot()
    g.save('g.jpg')
    r = []
    hi = h2 - h1
    target_count = 9
    for i in range(target_count):
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
    d, o = r[-1]
    if d is None:
        r[-1] = 9999, o
    for i in range(len(r))[:-1][::-1]:
        d, o = r[i]
        if d is None:
            r[i] = r[i+1][0], o
    return r


def wnd_target_operation(idx: int, op: Callable[[float, float], None]) -> None:
    hi = h2 - h1
    ht = h1+hi*(idx+0.5)
    wnd.click(-w2, ht)
    sleep(1)
    x, y = -0.36, ht+idx*0.1044
    x %= 1
    y %= 1
    op(x, y)
    sleep(1)


def wnd_unlock_target(target_idx: int) -> None:
    y = 0.07
    x1, x2 = 0.30, 0.36
    x = x1 + target_idx * (x2 - x1)
    wnd.click(x, y)
    sleep(1)
    wnd.click(x, y + 0.125)
    sleep(1)


def wnd_unlock_all_targets() -> None:
    for i in range(MAX_LOCK_TARGETS)[::-1]:
        wnd_unlock_target(i) 

    
def wnd_lock_target(idx: int) -> None:
    wnd_target_operation(0, lambda x, y: wnd.click(x, y))


def wnd_distance_select(x1: float, y1: float, dist: float) -> None:
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


def wnd_approach_target(idx: int, dist: Optional[float] = None) -> None:
    if dist is None: 
        fn = wnd.click
    else:
        fn = lambda x, y: wnd_distance_select(x, y, dist)
    wnd_target_operation(1, fn)


def wnd_orbit_target(idx: int, dist: Optional[float] = None) -> None:
    if dist is None: 
        fn = wnd.click
    else:
        fn = lambda x, y: wnd_distance_select(x, y, dist)
    wnd_target_operation(2, fn)


def wnd_activate_device(col: int, row: int) -> None:
    wi, hi = 0.04470, 0.08287
    w, h = wi*(2*row+1), hi*(2*col+1)
    wnd.click(-w, -h)
    sleep(1)


def wnd_mine_and_orbit(idx: int, dist: float) -> None:
    wnd_lock_target(idx)
    wnd_activate_device(0, 0)
    wnd_activate_device(0, 1)
    wnd_orbit_target(idx, dist)


@change_aspect_while_fail
def get_storage_percent() -> float:
    
    def process_img(img):
        return img * 2
    
    g = wnd.screenshot()[
        0.029:0.070,
        0.145:0.173,
        :
    ]
    g = g.map(process_img)
    g.save('storage.jpg')
    perc = g.ocr(numbers=True)

    if perc[-1] != '%':
        raise NotImplementedError()
    return parse_prefix_float(perc)
    

def get_opt_ore_targets(ores) -> List[Tuple[int, Ore]]:
    ores = [
        (i, d, o) 
        for i, (d, o) \
        in enumerate(ores)
    ]
    ores = [
        (i, d, o) \
        for i, d, o in ores \
        if o != Ore.Unknown and d <= MAX_MINER_RANGE
    ]
    ores = sorted(
        ores, 
        key=lambda x: x[2].market_price_per_volume, 
        reverse=True
    )
    targets = [i for i, _, _ in ores[:MAX_LOCK_TARGETS]]
    return targets


def main():
    # print(get_storage_percent())
    # wnd_orbit_target(0, 65)
    targets = wnd_refresh_target_list(0, need_stop=True)
    ores = [(d, Ore.from_text(t)) for d, t in targets]
    print(ores)
    targets = get_opt_ore_targets(ores)
    print(targets)
    if len(targets) > 0:
        wnd_unlock_all_targets()
        wnd_mine_and_orbit(targets[0], 2)
