"""应用程序"""

import inspect
import json
from typing import Callable, Any
import asyncio
from pydantic import BaseModel, ValidationError
from .stream import StdioStream
from .router import RPCRouter
from .middleware import MiddlewareManager
from ..general.jsonrpc_model import *
from ..general.errors import *


class IOWrite:
    """写入依赖, 用于在方法中注入写入依赖, 可以在方法内主动写入响应"""

    def __init__(self, app: "RPCServer"):
        self.__app = app

    async def write(self, response: JSONRPCResponse | dict) -> None:
        if isinstance(response, dict):
            response = JSONRPCResponse(**response)
        await self.__app.write_line(response)


class RPCServer(StdioStream, RPCRouter):
    """RPC 服务器"""

    def __init__(
        self, server_name: str = "app", label: str = "", version: str = "v0.1.0"
    ):
        """
        Args:
            server_name: 服务器名称 默认 "app"
        """
        self.server_name = server_name
        self.version = version

        StdioStream.__init__(self)
        RPCRouter.__init__(self, server_name, label)

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
                # Pydantic 模型参数
                if (
                    inspect.isclass(ann)
                    and issubclass(ann, BaseModel)
                    and isinstance(params, dict)
                ):
                    # bound_args[name] = ann(**params)
                    bound_args[name] = ann(**params[name])
                # 注入Stdio写依赖
                elif ann is IOWrite:
                    bound_args[name] = IOWrite(self)
                # 普通参数
                elif name in params:
                    bound_args[name] = params[name]
                # 默认参数
                else:
                    bound_args[name] = param.default

            if inspect.iscoroutinefunction(func):
                result = await func(**bound_args)
            else:
                result = func(**bound_args)

            return JSONRPCResponse(id=request_id, result=result)

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
                    error = JSONRPCError(
                        id=e.from_id, error=RPCErrorDetail.model_validate(e.to_dict())
                    )
                    await self.write_line(error)
        except Exception as e:
            server_error = RPCServerError(code=-32099, message=f"未处理异常: {str(e)}")
            error = JSONRPCError(
                error=RPCErrorDetail.model_validate(server_error.to_dict())
            )
            await self.write_line(error)
        finally:
            if hasattr(self, "writer") and self.writer:
                self.close()

    def runserver(self):
        asyncio.run(self._run())

    def get_docs_json(self) -> dict:
        """生成当前服务的文档描述数据"""

        def is_pydantic_model(annotation: Any) -> bool:
            return isinstance(annotation, type) and issubclass(annotation, BaseModel)

        def serialize_params(func: Callable):
            params_data = []
            signature = inspect.signature(func)
            for param in signature.parameters.values():
                annotation = param.annotation

                # 跳过内部注入类型
                if annotation is IOWrite:
                    continue

                item: dict[str, Any] = {
                    "name": param.name,
                    "kind": param.kind.name,
                    "required": param.default is inspect._empty,
                }

                if annotation is inspect._empty:
                    item["type"] = None
                elif is_pydantic_model(annotation):
                    item["type"] = annotation.__name__
                    item["schema"] = annotation.model_json_schema()
                elif isinstance(annotation, type):
                    item["type"] = annotation.__name__
                else:
                    item["type"] = str(annotation)

                default = param.default
                if default is inspect._empty:
                    item["default"] = None
                else:
                    try:
                        json.dumps(default)
                        item["default"] = default
                    except TypeError:
                        item["default"] = repr(default)

                params_data.append(item)
            return params_data

        def is_custom_type(annotation: Any) -> bool:
            if not isinstance(annotation, type):
                return False
            return annotation.__module__ not in {"builtins", "typing"}

        def serialize_results(func: Callable):
            signature = inspect.signature(func)
            annotation = signature.return_annotation

            if annotation is inspect._empty or annotation is None:
                return []

            item: dict[str, Any] = {}
            if is_pydantic_model(annotation):
                item["type"] = annotation.__name__
                item["schema"] = annotation.model_json_schema()
            elif isinstance(annotation, type):
                item["type"] = annotation.__name__
            else:
                item["type"] = str(annotation)

            if isinstance(annotation, type) and is_custom_type(annotation):
                doc = inspect.getdoc(annotation) or ""
                if doc:
                    item["doc"] = doc

            return [item]

        def walk(router: RPCRouter, full_prefix: str = ""):
            methods = []
            for method_name, (func, label) in router.methods.items():
                path = ".".join(filter(None, [full_prefix, method_name]))
                methods.append(
                    {
                        "name": method_name,
                        "label": label,
                        "path": path,
                        "doc": inspect.getdoc(func) or "",
                        "params": serialize_params(func),
                        "results": serialize_results(func),
                    }
                )

            middlewares = []
            for middleware, label in getattr(router.middlewares, "get_full")():
                middlewares.append(
                    {
                        "name": middleware.__name__,
                        "label": label,
                        "doc": inspect.getdoc(middleware) or "",
                    }
                )

            routers = {}
            for prefix, sub_router in router.sub_routers.items():
                sub_prefix = ".".join(filter(None, [full_prefix, prefix]))
                routers[prefix] = walk(sub_router, sub_prefix)

            return {
                "label": getattr(router, "label", ""),
                "methods": methods,
                "middlewares": middlewares,
                "routers": routers,
            }

        tree = walk(self, "")
        return {
            "server_name": self.server_name,
            "version": self.version,
            "label": getattr(self, "label", ""),
            "methods": tree["methods"],
            "middlewares": tree["middlewares"],
            "routers": tree["routers"],
        }
