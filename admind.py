import logging
import sys
from aiohttp import web
import socketio
import json
import time
import aiohttp_session
import asyncio
from http.cookies import SimpleCookie

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


with open('admin.json', encoding='utf-8') as f:
    _CONFIG = json.load(f)
HOST = _CONFIG['host']
PORT = _CONFIG['port']


STATIC_PATH = './admin/build/'

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())

with open('authorized_tokens.json', encoding='utf-8') as f:
    _TOKENS = json.load(f)
authorized_tokens = set(_TOKENS)


async def index(request):
    cookie_str = request.headers.get('Cookie', '')
    cookie = SimpleCookie()
    cookie.load(cookie_str)
    token = None
    if 'token' in cookie:
        token = cookie['token'].value
    if token not in authorized_tokens:
        raise web.HTTPSeeOther(location="/login.html")
    with open(STATIC_PATH + 'index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

app.router.add_route('*', '/', index)
app.router.add_route('*', '/index.html', index)
app.router.add_static('/', path=STATIC_PATH)


clients = set()
slaves = {}


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

    task = interval_5_sec()
    asyncio.get_event_loop().create_task(task)

    await asyncio.Event().wait()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
