
class StorageCounter():

    def __init__(self, max_tick) -> None:
        self._arr = []
        self._max_tick = max_tick

    def add_and_test(self, value) -> bool:
        if len(self._arr) < self._max_tick:
            self._arr.append(value)
        elif len(self._arr) == self._max_tick:
            self._arr = self._arr[1:] + [value]
        else:
            raise NotImplementedError()
        # print([value != _ for _ in self._arr])
        if len(self._arr) < self._max_tick:
            return True
        else:
            return any(value != _ for _ in self._arr)

    def get(self):
        if len(self._arr) == 0:
            return None
        return self._arr[-1]

    def clear(self):
        self._arr = []
