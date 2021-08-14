import json
from enum import Enum


with open('ore.json', encoding='utf-8') as f:
    _ORE_DATABASE = {_['id']: _ for _ in json.load(f)}


class Ore(Enum):

    Unknown = 0         # ???
    Veldspar = 1        # 凡晶石
    Scordite = 2        # 灼烧岩
    Pyroxeres = 3       # 干焦岩
    Plagioclase = 4     # 斜长岩
    Omber = 5           # 奥贝尔石
    Kernite = 6         # 水硼砂
    Jaspet = 7          # 杰斯贝矿
    Hemorphite = 8      # 希莫非特
    Hedbergite = 9      # 同位原矿
    Spodumain = 10      # 灰岩
    Ochre = 11          # 黑赭石
    Gneiss = 12         # 片麻岩
    Crokite = 13        # 克洛基石
    Bistot = 14         # 双多特石
    Arkonor = 15        # 艾克诺岩
    Mercoxit = 16       # 基腹断岩

    @staticmethod
    def from_text(text) -> 'Ore':
        for j in _ORE_DATABASE.values():
            if j['name'] in text:
                return Ore(j['id'])
        return Ore.Unknown

    def __getitem__(self, item):
        return _ORE_DATABASE[self.value][item]

    @property
    def market_price(self):
        return self['market_price']

    @property
    def volume(self):
        return self['volume']

    @property
    def market_price_per_volume(self):
        return self.market_price / self.volume

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        if self is Ore.Unknown:
            return "<???>"
        return "<{}:{}>".format(self['name'], self.value)


if __name__ == "__main__":
    texts = ['小行星[斜长岩]〕', '小行星[斜长岩〕', '小行星[灼烧岩〕', '小行星[奥贝尔石]', '小行星[斜长岩〕']
    ores = [Ore.from_text(_) for _ in texts]
    print(ores)
