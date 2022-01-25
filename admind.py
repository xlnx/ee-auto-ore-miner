import logging
import sys
from typing import Awaitable, Callable
from aiohttp import web
import socketio
import json
import time
import aiohttp_session

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
authorized_tokens = set(
    'SA0USrTuEyQ2U1dOp-eDBA'
)


async def index(request):
    session = await aiohttp_session.get_session(request)
    token = session.get("token")
    if token not in authorized_tokens:
        raise web.HTTPSeeOther(location="/login")
    with open(STATIC_PATH + 'index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

app.router.add_route('*', '/', index)
app.router.add_static('/', path=STATIC_PATH)


clients = set()
slaves = {}


def heartbeat_impl(sid):
    slaves[sid]['heartbeat'] = time.time()


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

# @sio.on('init')
# async def init()


# class AdminServer():
#     def __init__(self) -> None:
#         sio.connect(f'http://{HOST}:{PORT}')

#     def heartbeat(self) -> None:
#         pass

#     def update_storage(self, perc: int) -> None:
#         self.heartbeat()


if __name__ == "__main__":
    web.run_app(app, port=PORT)
    # static_files = {
    #     '/': './admin/build/',
    # }
    # sio = socketio.Server()
    # app = socketio.WSGIApp(sio, static_files=static_files)

    # import eventlet
    # eventlet.wsgi.server(eventlet.listen(('', PORT)), app)
    # admin = AdminServer()

    # from http.server import HTTPServer, SimpleHTTPRequestHandler

    # class Handler(SimpleHTTPRequestHandler):
    #     def __init__(self, *args, **kwargs) -> None:
    #         super().__init__(*args, **kwargs, directory='./admin/build')

    #     def log_message(self, fmt, *args) -> None:
    #         pass

    # httpd = HTTPServer(('localhost', PORT), Handler)

    # print(f'serving at port: {PORT}')
    # httpd.serve_forever()
