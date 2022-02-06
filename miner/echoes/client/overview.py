# from config import config
import logging
from typing import List, Optional, Tuple
from .window import Window
from .util import ocr, parse_prefix_float, sleep, try_again


class Overview():
    def __init__(self, window: Window) -> None:
        self._wnd = window
        self._curr = -1

    @property
    def item_height(self) -> int:
        return self._wnd.y(86)

    # ok
    def open(self, idx: int, fast: bool = False) -> None:
        if self._curr != idx:
            logging.debug('overview.open %d', idx)
            x = self._wnd.width - self._wnd.y(300)
            self._wnd.tap(x, self._wnd.y(30))
            self._wnd.tap(x, self._wnd.y(160) + self.item_height * idx)
            if not fast:
                sleep(1000)
            self._curr = idx

    # ok
    @try_again
    def list(self, max_items: int = 5, cand_alphabet: Optional[str] = None) -> List[Tuple[float, str]]:
        logging.debug('overview.list %d', max_items)
        x1 = self._wnd.width - self._wnd.y(389)
        x2 = self._wnd.width - self._wnd.y(78)
        y1 = self._wnd.y(67)
        y2 = self._wnd.y(537)
        img = self._wnd.screenshot((x1, y1, x2, y2))
        li = []
        for i in range(0, max_items):
            di = img.crop((self._wnd.y(36), self.item_height * i,
                           self._wnd.y(105), self.item_height * i + 52))
            di = ocr(di, cand_alphabet="0123456789.", single_line=True)
            ui = img.crop((self._wnd.y(36), self.item_height * i + 50,
                           self._wnd.y(105), self.item_height * (i + 1)))
            ui = ocr(ui, cand_alphabet="千米天文单位", single_line=True)
            ti = img.crop((self._wnd.y(108), self.item_height * i,
                           self._wnd.y(300), self.item_height * (i + 1)))
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
        x1 = self._wnd.width - self._wnd.y(389)
        x2 = self._wnd.width - self._wnd.y(78)
        y1 = self._wnd.y(67)
        y2 = self._wnd.y(537)
        img = self._wnd.screenshot((x1, y1, x2, y2))
        li = []
        for i in range(0, max_items):
            ti = img.crop((self._wnd.y(108), self.item_height * i,
                           self._wnd.y(300), self.item_height * (i + 1)))
            ti = ocr(ti, cand_alphabet=cand_alphabet)
            if ti == '':
                break
            li.append(ti)
        logging.debug('overview.list_fast %s', li)
        return li

    # ok
    def target_op(self, idx: int, op_idx: int, dt: int = 300) -> None:
        logging.debug('overview.target_op %d, %d', idx, op_idx)
        y = self._wnd.y(67) + self.item_height * idx
        self._wnd.tap(self._wnd.width - self._wnd.y(300), y + self._wnd.y(50))
        self._wnd.tap(self._wnd.width - self._wnd.y(600), y +
                      self._wnd.y(95) * op_idx + self._wnd.y(50), dt)
