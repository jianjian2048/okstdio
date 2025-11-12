import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from okstdio.client import RPCClient
from okstdio.general.jsonrpc_model import *
from okstdio.general.errors import *

# 要使用公共模块需要使用 python -m example.client 启动
# 否则需要把客户端移动到根目录并使用 from example.schemas import * 导入.
# from .schemas import *

# 设置日志
FORMAT = "[%(asctime)s] %(levelname)s @%(name)s > %(message)s"
DATEFMT = "%m-%d %H:%M:%S"
LOG_HANDLER = RotatingFileHandler(
    filename="example/assets/client.log",
    maxBytes=2 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
)
LOG_HANDLER.setFormatter(logging.Formatter(FORMAT, DATEFMT))

# 配置 root logger，确保不输出到 stdout
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers.clear()  # 清除所有默认 handler
root_logger.addHandler(LOG_HANDLER)


async def view_fighting(client: RPCClient, task_id: str, queue: asyncio.Queue):

    for _ in range(10):
        response = await queue.get()
        print(response.model_dump_json())

    future = await client.send("hero.stop_dungeon", {"task_id": task_id})
    response = await future
    print(response.model_dump_json())


async def main():

    async with RPCClient("example_client") as client:

        await client.start("example.server")
        future = await client.send("healthy")
        response = await future
        print(response.model_dump_json())

        hero_name = "heimi"
        future = await client.send("hero.create", {"hero": {"hero_name": hero_name}})
        response = await future
        print(response.model_dump_json())

        future = await client.send("hero.dungeon", {"hero_name": hero_name})
        response = await future
        task_id = response.result.get("task_id")
        queue = client.add_listen_queue(task_id)
        await view_fighting(client, task_id, queue)


if __name__ == "__main__":
    asyncio.run(main())
