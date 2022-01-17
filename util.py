import logging
import time
from cnocr import CnOcr
from PIL import Image, ImageEnhance
import numpy as np
from itertools import takewhile

_ocr = CnOcr()


def sleep(ms: int):
    time.sleep(float(ms) / 1000)


def now_sec() -> float:
    return time.time()


def is_similar(rgb1, rgb2, d: float = 30) -> bool:
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    return -d < r1-r2 < d and -d < g1-g2 < d and -d < b1-b2 < d


def ocr(img: Image, numbers: bool = False) -> str:
    img = ImageEnhance.Brightness(img).enhance(1.3)
    res = _ocr.ocr(np.array(img))
    res = ["".join(_) for _ in res]
    res = "".join(res)
    if numbers:
        res = res\
            .replace(',', '')\
            .replace('，', '')\
            .replace('D', '0')\
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
            .replace('q', '9')\
            .replace('□', '0')
    return res


def parse_prefix_float(text):
    return float(''.join(takewhile(lambda x: str.isdigit(x) or x == '.', text)))


def try_again(func):
    def _(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception:
                logging.info('try again')
                args[0].swipe(700, 400, 900, 500)
                continue
    return _
