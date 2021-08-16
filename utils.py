import mss
import math
import time
import random
import win32gui
import pyautogui
import numpy as np
from cnocr import CnOcr
from PIL import Image
from itertools import takewhile


ocr = CnOcr()


def numpy_flip(im):
    """ Most efficient Numpy version as of now. """
    frame = np.array(im, dtype=np.uint8)
    return np.flip(frame[:, :, :3], 2)


def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    rect = win32gui.GetWindowRect(hwnd)
    return rect


def parse_prefix_int(text):
    return int(''.join(takewhile(str.isdigit, text)))


def parse_prefix_int_or(text, default):
    try:
        return parse_prefix_int(text)
    except:
        return default


def parse_prefix_float(text):
    return float(''.join(takewhile(lambda x: str.isdigit(x) or x == '.', text)))


def parse_prefix_float_or(text, default):
    try:
        return parse_prefix_float(text)
    except:
        return default


def sleep(sec):
    time.sleep(sec)


class WindowScreenshot():

    def __init__(self, data, window):
        self.data = np.array(data)
        self.window = window

    def __getitem__(self, key):
        def f(x, ix):
            if x is None:
                return None
            return ix(x)
        x, y, z = key
        if isinstance(y, slice):
            y = slice(*[
                f(_, self.window.iy)
                for _ in [y.start, y.stop, y.step]
            ])
        else:
            y = self.window.iy(y)
        if isinstance(x, slice):
            x = slice(*[
                f(_, self.window.ix)
                for _ in [x.start, x.stop, x.step]
            ])
        else:
            x = self.window.ix(x)
        key = y, x, z
        return WindowScreenshot(
            self.data[key],
            self.window
        )

    def map(self, f):
        data = f(self.data)
        return WindowScreenshot(data, self.window)

    def save(self, file):
        img = Image.fromarray(self.data)
        img.save(file)

    def ocr(self, numbers=False):
        res = ocr.ocr(self.data)
        res = ["".join(_) for _ in res]
        res = "".join(res)
        if numbers:
            res = res\
                .replace(',', '')\
                .replace('，', '')\
                .replace('O', '0')\
                .replace('@', '0')\
                .replace('o', '0')\
                .replace('l', '1')\
                .replace('I', '1')\
                .replace('i', '1')\
                .replace('S', '5')\
                .replace('s', '5')\
                .replace('b', '6')\
                .replace('B', '8')\
                .replace('q', '9')
        return res


def _absolute(*dims):
    # dims = [_.lower() for _ in dims]
    def inner(func):
        def inner_impl(self, *args, **kwargs):
            args = list(args)
            for idx, dim in enumerate(dims):
                if dims[idx] == 0:
                    args[idx] = self.rix(args[idx])
                elif dims[idx] == 1:
                    args[idx] = self.riy(args[idx])
                else:
                    raise NotImplementedError()
            return func(self, *args, **kwargs)
        return inner_impl
    return inner


class Window():

    def __init__(self, rect):
        self.rect = rect
        self.x1, self.y1, self.x2, self.y2 = rect
        self.w = self.x2 - self.x1
        self.h = self.y2 - self.y1

    def ix(self, x):
        return int(self.w * x)

    def iy(self, y):
        return int(self.h * y)

    def rix(self, x):
        x %= 1
        return self.x1 + self.ix(x)

    def riy(self, y):
        y %= 1
        return self.y1 + self.iy(y)

    def screenshot(self):
        with mss.mss() as sct:
            img = sct.grab(self.rect)
            data = numpy_flip(img)
            scr = WindowScreenshot(data, self)
        return scr

    @_absolute(0, 1)
    def move_to(self, x, y):
        pyautogui.moveTo(x, y)

    @_absolute(0, 1)
    def click(self, x, y):
        pyautogui.leftClick(x, y)

    def close(self):
        pyautogui.leftClick(self.x2-3, self.y1-3)
        sleep(1)
        self.click(0.567, 0.515)

    @_absolute(0, 1, 0, 1)
    def drag_ease(self, x1, y1, x2, y2, dur=1, ease=pyautogui.easeInQuad):
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        duration = dur * (0.8 + dist * 1.0 / 500)
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(
            x2, y2,
            button='left',
            duration=duration,
            tween=ease
        )
