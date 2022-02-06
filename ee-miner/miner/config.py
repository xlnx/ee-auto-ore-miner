from typing import Any


class ConfigDict:
    def __init__(self, val: Any = {}) -> None:
        self._obj = val

    def __getattr__(self, key: str) -> Any:
        if key in self._obj:
            val = self._obj[key]
            if isinstance(val, dict):
                return ConfigDict(val)
            return val
        raise KeyError(key)

    def load(self, obj: Any) -> None:
        self._obj = obj

    def contains(self, key: str) -> bool:
        return key in self._obj

    def get(self, key: str, default) -> Any:
        if key in self._obj:
            return self.__getattr__(key)
        return default


config = ConfigDict()
