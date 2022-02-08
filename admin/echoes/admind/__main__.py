import logging
import threading
import traceback
import sys
from typing import Any, Dict, Iterable, Type, TypeVar
from aiohttp import web
import socketio
import time
import aiohttp_session
import asyncio
import yaml
import argparse
from http.cookies import SimpleCookie
from .bot import Bot
import os
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--config', required=True, action='store',
                    help='path to yaml config file')

args = parser.parse_args()


file_handler = logging.FileHandler(filename='admin.log', encoding='utf-8')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.WARNING,
    format=u'[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers,
    force=True
)

logger = logging.getLogger("admin")
logger.setLevel(logging.INFO)


def load_config():
    with open(args.config, 'r', encoding='utf-8') as f:
        conf = yaml.load(f.read(), Loader=yaml.FullLoader)
    global PORT, TOKENS, BOT, WARN, EMERGENCY
    PORT = conf.get('port', 5700)
    TOKENS = set(conf['authorized_tokens'])
    bot_conf = conf.get('bot', {})
    host = bot_conf.get('host', None)
    port = bot_conf.get('port', None)
    group_ids = bot_conf.get('group_ids', [])
    online_group_ids = bot_conf.get('online_group_ids', group_ids)
    threshold_conf = bot_conf.get('threshold', {})
    WARN = threshold_conf.get('warn', 3)
    EMERGENCY = threshold_conf.get('emergency', 8)
    BOT = Bot(host=host, port=port, group_ids=group_ids,
              online_group_ids=online_group_ids)


STATIC_PATH = os.path.join(dir_path, 'build/')

load_config()

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())


async def index(request):
    cookie_str = request.headers.get('Cookie', '')
    cookie = SimpleCookie()
    cookie.load(cookie_str)
    token = None
    if 'token' in cookie:
        token = cookie['token'].value
    if token not in TOKENS:
        raise web.HTTPSeeOther(location="/login.html")
    with open(STATIC_PATH + 'index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

app.router.add_route('*', '/', index)
app.router.add_route('*', '/index.html', index)
app.router.add_static('/', path=STATIC_PATH)

T = TypeVar('T')


class Entity():

    pool: Dict[str, 'Entity'] = {}

    @staticmethod
    def filter(role: Type[T]) -> Iterable[T]:
        for _, ent in Entity.pool.items():
            if isinstance(ent, role):
                yield ent

    @property
    def sid(self) -> str:
        return self._sid

    def __init__(self, sid: str) -> None:
        self._sid = sid

    async def connect(self, *args) -> None:
        assert self.sid not in Entity.pool
        Entity.pool[self.sid] = self
        logger.info(f'{type(self).__name__} connected: {self.sid}')

    async def disconnect(self) -> None:
        logger.info(f'{type(self).__name__} disconnected: {self.sid}')
        del Entity.pool[self.sid]


clients = set()
slaves = {}
systems = {}

mutex = threading.Lock()

prev_lvl = 0


@sio.event
async def disconnect(sid):
    if sid in Entity.pool:
        await Entity.pool[sid].disconnect()


@sio.event
async def dispatch(sid, evt: str, *args):
    if sid not in Entity.pool:
        if evt == 'init':
            role, *args = args
            cls = globals().get(role, None)
            if cls is None:
                logging.warning(f'role {role} not found')
                return
            await cls(sid).connect(*args)
        else:
            logging.warning(f'invalid event: {evt}')
    else:
        obj = Entity.pool[sid]
        fn = getattr(obj, evt, None)
        if fn is not None:
            try:
                await fn(*args)
            except Exception:
                print(traceback.format_exc())
                logging.warning(f'call {type(obj).__name__}.{evt} failed')
        else:
            logging.warning(f'{type(obj).__name__} has no event: {evt}')


""" CLIENTS """


class Client(Entity):
    @staticmethod
    async def broadcast(evt: str, *args) -> None:
        logger.debug(f'broadcast {evt}')
        for cl in Entity.filter(Client):
            await sio.emit(evt, *args, room=cl.sid)

    async def connect(self, *args) -> None:
        await super().connect(*args)
        slaves = {e.sid: e.data for e in Entity.filter(Slave)}
        await sio.emit('update_slave', slaves, room=self.sid)

    async def task(self, sid, *args):
        assert sid in Entity.pool
        await sio.emit('slave_task', *args, room=sid)


class Slave(Entity):
    def __init__(self, sid: str) -> None:
        super().__init__(sid)
        self.data = {'type': type(self).__name__}

    @property
    def state(self) -> Dict[str, Any]:
        return self.data['state']

    async def connect(self, data, *args) -> None:
        await super().connect(*args)
        self.data.update(data)
        self.data['sid'] = self.sid
        await self.heartbeat()
        await self.sync()

    async def heartbeat(self):
        self.data['heartbeat'] = time.time()
        self.data['dead'] = 0

    async def disconnect(self) -> None:
        for client in Entity.filter(Client):
            await sio.emit('remove_slave', self.sid, room=client.sid)
        await super().disconnect()

    async def sync(self) -> None:
        await Client.broadcast('update_slave', {self.sid: self.data})


class Miner(Slave):
    async def update(self, key, value):
        self.state[key] = value
        await self.heartbeat()
        await self.sync()

    async def update_local(self, x, y, z):
        if 'system' in self.state:
            s = self.state['system']
            mutex.acquire()
            system = systems.setdefault(s, {})
            t = time.time()
            t0 = system.setdefault('timestamp', t)
            x0 = system.setdefault('x', x)
            y0 = system.setdefault('y', y)
            z0 = system.setdefault('z', z)
            system['timestamp'] = t
            system['x'] = x
            system['y'] = y
            system['z'] = z
            mutex.release()
            dt = round(t - t0)
            dx = x - x0
            dy = y - y0
            lvl = 0
            n = 0
            if x + y >= EMERGENCY:
                n = EMERGENCY
                lvl = 2
            elif x + y >= WARN:
                n = WARN
                lvl = 1
            global prev_lvl
            enable = False
            if lvl != prev_lvl:
                enable = lvl > prev_lvl
                prev_lvl = lvl
            if (dx != 0 or dy != 0) and enable:
                # def f(dx):
                #     return f'增加了{dx}' if dx > 0 else f'减少了{-dx}'
                # ms = []
                # if dx != 0:
                #     ms.append(f'{f(dx)}红')
                # if dy != 0:
                #     ms.append(f'{f(dy)}白')
                # ms = '，'.join(ms)
                id = self.data['device'].get('id', '')
                if not id:
                    id = '热心群众'
                # ，{dt}秒内{ms}
                message = f'【{s}】{x}红{y}白，超过阈值{n}\n【{id}】'
                await BOT.prompt(message)

        self.state['local'] = [x, y, z]
        await self.heartbeat()
        await self.sync()


async def interval_5_sec():
    while True:
        t1 = time.time()
        for slave in Entity.filter(Slave):
            if 'heartbeat' in slave.data:
                t0 = slave.data['heartbeat']
                if t1 - t0 > 120:
                    slave.data['dead'] = 1
                    await slave.sync()
        await asyncio.sleep(5)


async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=PORT)
    await site.start()
    print(f"serving on http://127.0.0.1:{PORT}")

    # task = interval_5_sec()
    # asyncio.get_event_loop().create_task(task)
    # asyncio.get_event_loop().create_task(bot.spawn())

    # await asyncio.Event().wait()
    await asyncio.gather(interval_5_sec(), BOT.spawn())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
