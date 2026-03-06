import asyncio
from okstdio.client import RPCClient
from rich import print
import logging

logging.basicConfig(level=logging.INFO)


async def test_client():

    async with RPCClient("test_server") as client:
        print("开始启动测试服务器")
        await client.start("tests.test_server")
        print("测试服务器启动完成")
        await client.send("hello", {})


if __name__ == "__main__":
    asyncio.run(test_client())
