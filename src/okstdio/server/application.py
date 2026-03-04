"""RPC 服务器模块

提供基于 Stdio 的 JSON-RPC 服务器实现，用于处理来自父进程的请求。
服务器通过标准输入输出与父进程进行 JSON-RPC 协议的消息交换。
"""

import inspect
import json
from typing import Callable, Any
import asyncio
from pydantic import BaseModel, ValidationError
from .stream import StdioStream
from .router import RPCRouter
from .middleware import MiddlewareManager
from .appdoc import AppDoc
from ..general.jsonrpc_model import *
from ..general.errors import *


class IOWrite:
    """写入依赖，用于在方法中注入写入依赖
    
    可以在方法内主动写入响应到父进程。
    通常用于需要服务器主动推送消息的场景（如实时更新、进度通知等）。
    
    例子：
        ```python
        @app.add_method()
        async def long_task(io_write: IOWrite):
            # 执行长时间任务
            for i in range(10):
                # 推送进度
                await io_write.write({"result": f"进度: {i * 10}%"})
                await asyncio.sleep(1)
        ```
    
    Args:
        app: 关联的 RPCServer 实例
    """

    def __init__(self, app: "RPCServer"):
        """初始化 IOWrite
        
        Args:
            app: 关联的 RPCServer 实例
        """
        self.__app = app

    async def write(self, response: JSONRPCResponse | dict) -> None:
        """写入响应到父进程
        
        Args:
            response: 响应对象，可以是 JSONRPCResponse 实例或字典
        
        例子：
            ```python
            # 使用字典
            await io_write.write({"result": {"status": "ok"}})
            
            # 使用 JSONRPCResponse
            await io_write.write(JSONRPCResponse(result={"status": "ok"}))
            ```
        """
        if isinstance(response, dict):
            response = JSONRPCResponse(**response)
        await self.__app.write_line(response)


class RPCServer(StdioStream, RPCRouter, AppDoc):
    """RPC 服务器
    
    基于 Stdio 的 JSON-RPC 服务器，用于处理来自父进程的请求。
    服务器通过标准输入输出与父进程进行 JSON-RPC 协议的消息交换。
    
    核心功能：
        - 路由注册和分发
        - 中间件支持
        - 参数自动校验（Pydantic 模型）
        - 依赖注入（如 IOWrite）
        - 自动生成 API 文档
    
    继承的基类：
        - StdioStream: 提供标准输入输出的读写能力
        - RPCRouter: 提供路由注册和分发功能
        - AppDoc: 提供 API 文档生成功能
    
    例子：
        ```python
        from okstdio.server import RPCServer, RPCRouter, IOWrite
        
        app = RPCServer("my_server", label="示例服务器")
        
        @app.add_method(name="hello", label="问候")
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        # 创建子路由
        user_router = RPCRouter("user")
        @user_router.add_method()
        def get_user(user_id: int) -> dict:
            return {"id": user_id, "name": "张三"}
        
        app.include_router(user_router)
        
        if __name__ == "__main__":
            app.runserver()
        ```
    
    Args:
        server_name: 服务器名称，默认 "app"
        label: 服务器标签/描述，默认 ""
        version: 服务器版本，默认 "v0.1.0"
    """

    def __init__(
        self, server_name: str = "app", label: str = "", version: str = "v0.1.0"
    ):
        """初始化 RPC 服务器
        
        Args:
            server_name: 服务器名称，默认 "app"
            label: 服务器标签/描述，默认 ""
            version: 服务器版本，默认 "v0.1.0"
        """
        self.server_name = server_name
        self.version = version

        StdioStream.__init__(self)
        RPCRouter.__init__(self, server_name, label)

    async def handle_request(self, request_string: str) -> JSONRPCResponse:
        """处理 JSON-RPC 请求
        
        解析请求、分发到对应的处理函数、返回响应。
        该方法会自动处理异常并返回适当的错误响应。
        
        Args:
            request_string: JSON 字符串格式的请求
        
        Returns:
            JSONRPCResponse: 响应对象
        
        Raises:
            RPCError: 当请求处理失败时
        
        处理流程：
            1. 解析 JSON 请求
            2. 验证 JSON-RPC 2.0 格式
            3. 分割路由路径
            4. 收集中间件
            5. 分发到处理函数
            6. 处理异常并返回错误响应
        """
        try:
            request: dict = json.loads(request_string)
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
                    raise RPCMethodNotFoundError(data=None, from_id=json_rpc_request.id)

                async def handler(request: JSONRPCRequest):
                    return await self.__execute_method(func, request.params, request.id)

                manager = MiddlewareManager()
                for mw in collected_middlewares:
                    manager.add(mw)

                # 将 json_rpc_request 作为参数传入, 因为中间件也需要.
                return await manager.run(json_rpc_request, handler)

            child = current.sub_routers.get(head)
            if child is None:
                raise RPCMethodNotFoundError(data=None, from_id=json_rpc_request.id)

            return await dispatch(child, tail)

        return await dispatch(self, segments)

    async def __execute_method(
        self, func: Callable, params: Any, request_id: str | int
    ):
        """执行方法
        
        解析函数签名、自动注入依赖、执行函数并返回结果。
        
        Args:
            func: 要执行的函数
            params: 请求参数
            request_id: 请求 ID
        
        Returns:
            JSONRPCResponse: 响应对象
        
        支持的参数类型：
            - Pydantic 模型：自动从字典创建实例
            - IOWrite：自动注入写入依赖
            - 普通类型：直接从 params 中获取
            - 默认参数：使用函数默认值
        
        异常处理：
            - ValidationError: 转换为 RPCInvalidParamsError
            - 其他异常：根据返回类型处理
        """
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

            # 如果返回的类型是 JSONRPCErrorDetail 则结果错误.
            # 这是函数内部判断出错误时应返回的对象.
            if isinstance(result, JSONRPCErrorDetail):
                return JSONRPCError(id=request_id, error=result)

            return JSONRPCResponse(id=request_id, result=result)

        except ValidationError as exc:
            raise RPCInvalidParamsError(
                data=exc.errors(
                    include_url=False, include_input=False, include_context=False
                ),
                from_id=request_id,
            )

    async def _runserver(self):
        """运行服务器主循环
        
        持续从标准输入读取请求，处理后写入标准输出。
        循环会在以下情况停止：
            - 对端关闭连接（EOF）
            - 发生未处理的异常
        """
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
                        id=e.from_id,
                        error=JSONRPCErrorDetail.model_validate(e.to_dict()),
                    )
                    await self.write_line(error)
        except Exception as e:
            server_error = RPCServerError(code=-32099, message=f"未处理异常: {str(e)}")
            error = JSONRPCError(
                error=JSONRPCErrorDetail.model_validate(server_error.to_dict())
            )
            await self.write_line(error)
        finally:
            if hasattr(self, "writer") and self.writer:
                self.close()

    def runserver(self):
        """启动服务器
        
        启动异步服务器主循环。
        该方法会阻塞直到服务器停止。
        
        例子：
            ```python
            if __name__ == "__main__":
                app.runserver()
            ```
        """
        asyncio.run(self._runserver())
