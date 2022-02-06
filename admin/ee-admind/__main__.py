import logging
import threading
import sys
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

with open(args.config, 'r', encoding='utf-8') as f:
    _CONFIG = yaml.load(f.read(), Loader=yaml.FullLoader)

HOST = _CONFIG['host']
PORT = _CONFIG['port']
TOKENS = set(_CONFIG['authorized_tokens'])
host = _CONFIG['bot']['host']
port = _CONFIG['bot']['port']
group_ids = _CONFIG['bot']['group_ids']
bot = Bot(host=host, port=port, group_ids=group_ids)


STATIC_PATH = os.path.join(dir_path, 'build/')

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


clients = set()
slaves = {}
systems = {}

mutex = threading.Lock()


def heartbeat_impl(sid):
    slaves[sid]['heartbeat'] = time.time()
    slaves[sid]['dead'] = 0


async def broadcast_slave_info(sid):
    logger.debug(f'broadcast slave {sid}')
    for client in clients:
        await sio.emit('update_slave', {sid: slaves[sid]}, room=client)


@sio.event
async def client_init(sid):
    logger.info(f'client connected: {sid}')
    await sio.emit('update_slave', slaves, room=sid)
    clients.add(sid)


@sio.event
async def slave_init(sid, device):
    assert sid not in slaves
    logger.info(f'slave connected: {sid}')
    slaves[sid] = {'device': device, 'sid': sid}
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)
    # print(slaves)


@sio.event
async def disconnect(sid):
    if sid in slaves:
        logger.info(f'slave disconnected: {sid}')
        for client in clients:
            await sio.emit('remove_slave', sid, room=client)
        del slaves[sid]
    elif sid in clients:
        logger.info(f'client disconnected: {sid}')
        clients.remove(sid)
    # print(f'disconnected: {sid}')


@sio.event
async def heartbeat(sid):
    heartbeat_impl(sid)


@sio.event
async def update_storage(sid, value):
    slaves[sid]['storage'] = value
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)
    # print(slaves)


@sio.event
async def update_system(sid, system):
    slaves[sid]['system'] = system
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)
    # print(slaves)


@sio.event
async def update_local(sid, x, y, z):
    if 'system' in slaves[sid]:
        s = slaves[sid]['system']
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
        if dx != 0 or dy != 0:
            def f(dx):
                return f'增加了{dx}' if dx > 0 else f'减少了{-dx}'
            ms = []
            if dx != 0:
                ms.append(f'{f(dx)}红')
            if dy != 0:
                ms.append(f'{f(dy)}白')
            ms = '，'.join(ms)
            id = slaves[sid]['device'].get('id', '')
            if not id:
                id = '热心群众'
            msg = f'【{s}】{x}红{y}白，总人数{z}，{dt}秒内{ms}\n--来自【{id}】'
            await bot.prompt(msg)

    slaves[sid]['local'] = [x, y, z]
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)
    # print(slaves)


@sio.event
async def update_status(sid, status):
    slaves[sid]['status'] = status
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)
    # print(slaves)


@sio.event
async def update_online(sid, online):
    slaves[sid]['online'] = online
    heartbeat_impl(sid)
    await broadcast_slave_info(sid)


@sio.event
async def slave_task(sid, dst, *args):
    assert sid in clients
    await sio.emit('slave_task', *args, room=dst)


async def interval_5_sec():
    while True:
        t1 = time.time()
        for sid, slave in slaves.items():
            if 'heartbeat' in slave:
                t0 = slave['heartbeat']
                if t1 - t0 > 120:
                    slave['dead'] = 1
                    await broadcast_slave_info(sid)
        await asyncio.sleep(5)


async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=PORT)
    await site.start()

    # task = interval_5_sec()
    # asyncio.get_event_loop().create_task(task)
    # asyncio.get_event_loop().create_task(bot.spawn())

    # await asyncio.Event().wait()
    await asyncio.gather(interval_5_sec(), bot.spawn())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
