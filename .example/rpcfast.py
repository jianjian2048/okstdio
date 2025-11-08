import sys
import json
import inspect
import asyncio
from typing import Any, Callable, Dict, Awaitable
from pydantic import BaseModel, ValidationError


class RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self, id=None):
        return {
            "jsonrpc": "2.0",
            "error": {"code": self.code, "message": self.message, "data": self.data},
            "id": id,
        }


class MiddlewareManager:
    def __init__(self):
        self.middlewares = []

    def add(self, func):
        self.middlewares.append(func)

    async def dispatch(self, handler, request):
        async def call_next(req):
            return await handler(req)

        for mw in reversed(self.middlewares):
            _next = call_next

            async def call_next(req, mw=mw, _next=_next):
                return await mw(req, _next)

        return await call_next(request)


class RPCServer:
    def __init__(self):
        self.methods: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.middleware = MiddlewareManager()

    def method(self, name: str = None):
        """注册 RPC 方法"""

        def decorator(func):
            self.methods[name or func.__name__] = func
            return func

        return decorator

    async def handle_request(self, req: Dict[str, Any]):
        """处理 JSON-RPC 请求"""
        try:
            if req.get("jsonrpc") != "2.0":
                raise RPCError(-32600, "Invalid Request")
            method_name = req.get("method")
            if method_name not in self.methods:
                raise RPCError(-32601, f"Method not found: {method_name}")

            func = self.methods[method_name]
            sig = inspect.signature(func)
            params = req.get("params", {})

            bound_args = []
            for name, param in sig.parameters.items():
                if param.annotation and issubclass(param.annotation, BaseModel):
                    bound_args.append(param.annotation(**params))
                else:
                    bound_args.append(params)

            # 调用处理函数
            result = (
                await func(*bound_args)
                if inspect.iscoroutinefunction(func)
                else func(*bound_args)
            )
            return {"jsonrpc": "2.0", "result": result, "id": req.get("id")}

        except ValidationError as e:
            return RPCError(-32602, "Invalid params", e.errors()).to_dict(req.get("id"))
        except RPCError as e:
            return e.to_dict(req.get("id"))
        except Exception as e:
            return RPCError(-32603, "Internal error", str(e)).to_dict(req.get("id"))

    def run(self):
        """启动 STDIO 主循环"""
        loop = asyncio.get_event_loop()
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            try:
                req = json.loads(line)
                result = loop.run_until_complete(self.handle_request(req))
                sys.stdout.write(json.dumps(result) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                err = RPCError(-32700, "Parse error").to_dict()
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
