from typing import Callable
from okstdio.server.application import RPCServer
from okstdio.server.router import RPCRouter

from okstdio.general.jsonrpc_model import JSONRPCRequest
from okstdio.general.errors import *

app = RPCServer(server_name="test_server")


@app.register_middleware()
async def log_middleware(request: JSONRPCRequest, call_next: Callable):
    print(f"app 前处理: {request}")
    # raise RPCError(code=-32600, message="test error")
    res = await call_next(request)
    print(f"app 后处理: {request}")
    return res


@app.register_method("index")
async def index():
    return "Hello, World!"


one = RPCRouter(prefix="one")


@one.register_method("index")
async def one_index():
    return "Hello, One!"


@one.register_method("api")
async def one_api():
    return "Hello, One API!"


two = RPCRouter(prefix="two")


@two.register_method("index")
async def two_index(name: str):
    print(f"two_index: {name}")
    return f"Hello, {name}"


@two.register_method("api")
async def two_api():
    return "Hello, Two API!"


one.include_router(two)
app.include_router(one)


async def main():
    try:
        test = await app.handle_request(
            '{"jsonrpc": "2.0", "method": "one.two.index", "params": {"name": "jianjian"}, "id": 10}'
        )
        print(test)
    except RPCError as e:
        print(e)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
