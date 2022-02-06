
import traceback
import logging
from typing import List


class Bot():
    def __init__(self, host: str, port: int, group_ids: List[int]) -> None:
        self._host = host
        self._port = port
        self._group_ids = group_ids
        self._bot = None
        if not len(group_ids):
            return
        try:
            import nonebot
        except ImportError:
            logging.warn('nonebot not installed')
            return
        nonebot.init()
        self._bot = nonebot.get_bot()

        @nonebot.on_websocket_connect
        async def _(event):
            await self.prompt('【已上线】')

    async def spawn(self):
        if self._bot is not None:
            await self._bot.asgi.run_task(host=self._host, port=self._port)

    async def prompt(self, msg: str):
        if self._bot is not None:
            for group_id in self._group_ids:
                try:
                    await self._bot.send_group_msg(group_id=group_id, message=msg)
                except Exception:
                    print(traceback.format_exc())
                    logging.warn(
                        f'send group message failed: {group_id} <= {msg}')
