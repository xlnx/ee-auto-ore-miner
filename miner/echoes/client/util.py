import os
import time
import logging
import numpy as np
from typing import Optional
from itertools import takewhile
from PIL import Image, ImageEnhance
from cnocr import CnOcr
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

_OCRS = {}


def sleep(ms: int):
    time.sleep(float(ms) / 1000)


def is_similar(rgb1, rgb2, d: float = 30) -> bool:
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    return -d < r1-r2 < d and -d < g1-g2 < d and -d < b1-b2 < d


def ocr(
    img: Image,
    cand_alphabet: Optional[str] = None,
    single_line: bool = False
) -> str:
    img = ImageEnhance.Brightness(img).enhance(1.3)
    if cand_alphabet not in _OCRS:
        _OCRS[cand_alphabet] = CnOcr(cand_alphabet=cand_alphabet)
    ocr = _OCRS[cand_alphabet]
    arr = np.array(img)
    if single_line:
        res, _ = ocr.ocr_for_single_line(arr)
    else:
        res = ocr.ocr(arr)
        res = ["".join(line) for line, _ in res]
    res = "".join(res)
    logging.debug("result is: " + res)
    return res


def get_static(file: str) -> str:
    return os.path.join(dir_path, 'static', file)


def parse_prefix_float(text):
    return float(''.join(takewhile(lambda x: str.isdigit(x) or x == '.', text)))


def try_again(func):
    def _(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.info('try again: ' + str(e))
                args[0].swipe(700, 400, 900, 500)
                continue
    return _
