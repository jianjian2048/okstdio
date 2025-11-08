"""中间件"""

from typing import Any, Callable, Awaitable, List
from ..general.jsonrpc_model import JSONRPCRequest


class MiddlewareManager:
    """### 中间件管理器

    #### 例子
    ```
    from okstdio.server.router import RPCRouter
    user_router = RPCRouter("user")

    @user_router.register_middleware()
    async def user_middleware(req, call_next):
        print(f"[user] 前处理: {req}")
        res = await call_next(req)
        print(f"[user] 后处理: {req}")
        return res
    ```

    #### 在这套实现里
    ```
        req:
            类型是 dict。
            它承载当前请求的上下文,如: {"method": "...", "params": {...}, "id": ...}
            被每个中间件沿途传递和可选地修改.
        call_next:
            类型是 Callable[[dict], Awaitable[dict]].
            你传入一个新的请求 dict, 它会继续调下一个中间件;
            如果已经是最后一个中间件, 就会调用最终的业务处理函数，
            返回 await 之后得到的响应 dict.
    ```
    """

    def __init__(self):
        self.middlewares: List[
            Callable[
                [JSONRPCRequest, Callable[[JSONRPCRequest], Awaitable[Any]]],
                Awaitable[Any],
            ]
        ] = []

    def add(
        self,
        middleware: Callable[
            [JSONRPCRequest, Callable[[JSONRPCRequest], Awaitable[Any]]], Awaitable[Any]
        ],
    ):
        self.middlewares.append(middleware)

    async def run(self, request: JSONRPCRequest, handler: Callable):
        """依次执行中间件链条"""

        async def next_middleware(index: int, req: JSONRPCRequest):
            if index < len(self.middlewares):
                return await self.middlewares[index](
                    req, lambda r: next_middleware(index + 1, r)
                )
            return await handler(req)

        return await next_middleware(0, request)
