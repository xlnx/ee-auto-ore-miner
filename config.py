import json
from typing import Any

with open('config.json', encoding='utf-8') as f:
    _CONFIG = json.load(f)


class ConfigDict:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        if key in self._obj:
            val = self._obj[key]
            if isinstance(val, dict):
                return ConfigDict(val)
            return val
        raise KeyError(key)

    def contains(self, key: str) -> bool:
        return key in self._obj

    def get(self, key: str, default) -> Any:
        if key in self._obj:
            return self.__getattr__(key)
        return default


config = ConfigDict(_CONFIG)
