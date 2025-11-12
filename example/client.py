import asyncio

from okstdio.client import RPCClient
from okstdio.general.jsonrpc_model import *
from okstdio.general.errors import *


async def main():

    async with RPCClient("example_client") as client:
        await client.start("example.server")
        future = await client.send("healthy")
        result = await future
        print(result.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
