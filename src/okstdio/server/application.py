"""应用程序"""

import inspect
import json
from typing import Callable

from pydantic import ValidationError
from .stream import StdioStream
from .router import RPCRouter
from .middleware import MiddlewareManager
from ..general.jsonrpc_model import *
from ..general.errors import *


class RPCServer(StdioStream, RPCRouter):
    """RPC 服务器"""

    def __init__(self, server_name: str = "app"):
        """
        Args:
            server_name: 服务器名称 默认 "app"
        """
        self.server_name = server_name
        StdioStream.__init__(self)
        RPCRouter.__init__(self, server_name)

    async def handle_request(self, request: str) -> JSONRPCResponse:
        """处理请求"""

        try:
            request: dict = json.loads(request)
        except json.JSONDecodeError:
            # 抛出语法解析错误
            raise RPCParseError()

        json_rpc_request = JSONRPCRequest.model_validate(request)
        method_router = json_rpc_request.method

        # 分割路由
        segments = method_router.split(".")
        if segments[0] == self.server_name:
            segments = segments[1:]

        collected_middlewares = []

        async def dispatch(current: RPCRouter, parts: list[str]) -> JSONRPCResponse:
            """分发请求"""
            collected_middlewares.extend(current.middlewares)

            head, *tail = parts
            if not tail:

                func = current.methods.get(head)
                if func is None:
                    raise RPCMethodNotFoundError(f"没有找到方法: {head}")

                async def handler(request: JSONRPCRequest):
                    return await self.__execute_method(func, request.params, request.id)

                manager = MiddlewareManager()
                for mw in collected_middlewares:
                    manager.add(mw)

                # 将 json_rpc_request 作为参数传入, 因为中间件也需要.
                return await manager.run(json_rpc_request, handler)

            child = current.sub_routers.get(head)
            if child is None:
                raise RPCMethodNotFoundError(f"没有找到子路由: {head}")

            return await dispatch(child, tail)

        return await dispatch(self, segments)

    async def __execute_method(
        self, func: Callable, params: Any, request_id: str | int
    ):
        """执行方法"""
        try:
            sig = inspect.signature(func)
            # 如果函数使用 Pydantic 参数，则自动校验
            bound_args = {}
            for name, param in sig.parameters.items():
                ann = param.annotation
                if (
                    inspect.isclass(ann)
                    and issubclass(ann, BaseModel)
                    and isinstance(params, dict)
                ):
                    bound_args[name] = ann(**params)
                elif name in params:
                    bound_args[name] = params[name]
                else:
                    bound_args[name] = param.default

            if inspect.iscoroutinefunction(func):
                result = await func(**bound_args)
            else:
                result = func(**bound_args)

            return JSONRPCResponse(result=result)

        except ValidationError as exc:
            raise RPCInvalidParamsError(
                data=exc.errors(
                    include_url=False, include_input=False, include_context=False
                ),
                from_id=request_id,
            )

    async def _run(self):
        try:
            while True:
                try:
                    request = await self.read_line()
                    if not request:
                        # 典型触发：对端关闭了写端或连接（到达 EOF），或本端/底层 transport 已被关闭
                        break
                    result = await self.handle_request(request)
                    await self.write_line(result)
                except RPCError as e:
                    ...
                except ValidationError as e:
                    ...
        except Exception as e:
            raise e
        finally:
            if hasattr(self, "writer") and self.writer:
                self.close()

    def run(self): ...
