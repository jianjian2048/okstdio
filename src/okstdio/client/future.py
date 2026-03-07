"""RPCFuture 模块

提供 Promise-like 的 awaitable 对象，支持 .then().error() 链式调用。
"""

import asyncio
import inspect
from typing import Any, Callable, Optional

from pydantic import BaseModel

from ..general.jsonrpc_model import JSONRPCResponse, JSONRPCError
from ..general.errors import _make_rpc_exception, RPCError


class RPCFuture:
    """Promise-like 的 awaitable 对象，支持链式调用

    例子：
        ```python
        # 简单调用
        result = await client.call("healthy")

        # 链式处理
        result = await client.call("method").then(handler).error(on_error)

        # 后台任务模式
        task = await client.call("method").then(handler, create_task=True)
        ```
    """

    def __init__(self, future: asyncio.Future, timeout: Optional[float] = None):
        self._future = future
        self._timeout = timeout
        self._then_handler: Optional[Callable] = None
        self._then_extra_params: dict = {}
        self._then_create_task: bool = False
        self._error_handler: Optional[Callable] = None

    def then(
        self,
        handler: Callable,
        extra_params: Optional[dict] = None,
        create_task: bool = False,
    ) -> "RPCFuture":
        """注册成功处理器，支持 BaseModel 类型注解自动注入"""
        self._then_handler = handler
        self._then_extra_params = extra_params or {}
        self._then_create_task = create_task
        return self

    def error(self, handler: Callable) -> "RPCFuture":
        """注册错误处理器，收到 JSONRPCError 时调用"""
        self._error_handler = handler
        return self

    async def _resolve(self) -> Any:
        if self._timeout is not None:
            response = await asyncio.wait_for(self._future, timeout=self._timeout)
        else:
            response = await self._future

        # 错误分支
        if isinstance(response, JSONRPCError):
            if self._error_handler:
                err = _make_rpc_exception(
                    code=response.error.code,
                    message=response.error.message,
                    data=response.error.data,
                    from_id=response.id,
                )
                result = self._error_handler(err)
                if asyncio.iscoroutine(result):
                    return await result
                return result
            raise _make_rpc_exception(
                code=response.error.code,
                message=response.error.message,
                data=response.error.data,
                from_id=response.id,
            )

        # 成功分支
        if self._then_handler:
            return await self._invoke_then(response)
        return response.result

    async def _invoke_then(self, response: JSONRPCResponse) -> Any:
        """用 inspect.signature 解析 handler 参数，自动注入"""
        if self._then_handler is None:
            raise ValueError("then() Not Registered handler function")

        sig = inspect.signature(self._then_handler)
        kwargs = {}

        for name, param in sig.parameters.items():
            annotation = param.annotation

            # 1. Pydantic BaseModel 子类 → response.result 验证为该类型
            if (
                annotation is not inspect.Parameter.empty
                and isinstance(annotation, type)
                and issubclass(annotation, BaseModel)
            ):
                kwargs[name] = annotation.model_validate(response.result)
            # 2. extra_params 中的同名参数
            elif name in self._then_extra_params:
                kwargs[name] = self._then_extra_params[name]
            # 3. 参数名为 "result" → 注入 response.result
            elif name == "result":
                kwargs[name] = response.result
            # 4. 参数名为 "response" → 注入完整 JSONRPCResponse
            elif name == "response":
                kwargs[name] = response
            # 5. 有默认值 → 使用默认值
            elif param.default is not inspect.Parameter.empty:
                continue
            # 6. 兜底 → 注入 response.result
            else:
                kwargs[name] = response.result

        result = self._then_handler(**kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    def __await__(self):
        if self._then_create_task and self._then_handler:

            async def _create():
                return asyncio.create_task(self._resolve())

            return _create().__await__()
        return self._resolve().__await__()
