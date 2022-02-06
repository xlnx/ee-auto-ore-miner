import time
import os
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)


def sleep(ms: int):
    time.sleep(float(ms) / 1000)


def get_static(file: str) -> str:
    return os.path.join(dir_path, 'static', file)
