from typing import Any, Callable, Awaitable, Dict, List
import asyncio
import inspect
import json
from pydantic import BaseModel, ValidationError

# ------------------------------------------------
# 中间件系统
# ------------------------------------------------


class MiddlewareManager:

    def __init__(self):
        self.middlewares: List[Callable[[dict, Callable], Awaitable[dict]]] = []

    def add(self, middleware: Callable[[dict, Callable], Awaitable[dict]]):
        self.middlewares.append(middleware)

    async def run(self, request: dict, handler: Callable):
        """依次执行中间件链条"""

        async def next_middleware(index: int, req: dict):
            if index < len(self.middlewares):
                return await self.middlewares[index](
                    req, lambda r: next_middleware(index + 1, r)
                )
            return await handler(req)

        return await next_middleware(0, request)


# ------------------------------------------------
# JSON-RPC 相关工具
# ------------------------------------------------


def jsonrpc_response(result: Any, id_: Any):
    return {"jsonrpc": "2.0", "result": result, "id": id_}


def jsonrpc_error(code: int, message: str, id_: Any = None):
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": id_}


# ------------------------------------------------
# RPCRouter 类似于 FastAPI 的 APIRouter
# ------------------------------------------------


class RPCRouter:
    def __init__(self):
        self.methods: Dict[str, Callable] = {}

    def method(self, name: str = None):
        """注册 RPC 方法"""

        def decorator(func):
            method_name = name or func.__name__
            self.methods[method_name] = func
            return func

        return decorator


# ------------------------------------------------
# 主 RPCServer
# ------------------------------------------------


class RPCServer:
    def __init__(self):
        self.methods: Dict[str, Callable] = {}
        self.middlewares = MiddlewareManager()

    def include_router(self, router: RPCRouter, prefix: str = ""):
        for name, func in router.methods.items():
            full_name = f"{prefix}.{name}" if prefix else name
            self.methods[full_name] = func

    def add_middleware(self, middleware: Callable):
        self.middlewares.add(middleware)

    def register_middleware(self):

        def decorator(func):
            self.middlewares.add(func)
            return func

        return decorator

    async def handle_request(self, request_json: str):
        try:
            request = json.loads(request_json)
            method = request.get("method")
            params = request.get("params", {})
            id_ = request.get("id")

            if not method or method not in self.methods:
                return json.dumps(jsonrpc_error(-32601, "Method not found", id_))

            async def handler(req):
                func = self.methods[req["method"]]
                return await self._execute_method(func, req, id_)

            response = await self.middlewares.run(request, handler)
            return json.dumps(response)

        except Exception as e:
            return json.dumps(jsonrpc_error(-32603, str(e)))

    async def _execute_method(self, func: Callable, request: dict, id_):
        try:
            sig = inspect.signature(func)
            params = request.get("params", {})

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

            return jsonrpc_response(result, id_)
        except ValidationError as e:
            return jsonrpc_error(-32602, f"Invalid params: {e}", id_)


# ------------------------------------------------
# 示例
# ------------------------------------------------


class Item(BaseModel):
    name: str
    price: float


router = RPCRouter()


@router.method("create_item")
async def create_item(item: Item):
    return {"message": f"Item '{item.name}' created!", "price": item.price}


@router.method("echo")
def echo(text: str):
    return {"echo": text}


# 注册路由到服务器
server = RPCServer()
server.include_router(router, prefix="item")


# 注册一个日志中间件
async def log_middleware(req, call_next):
    print(f"[LOG] Request: {req}")
    res = await call_next(req)
    print(f"[LOG] Response: {res}")
    return res


server.add_middleware(log_middleware)


@server.register_middleware()
async def log_middleware_2(req, call_next):
    print(f"[LOG2] Request: {req}")
    res = await call_next(req)
    print(f"[LOG2] Response: {res}")
    return res


# ------------------------------------------------
# 测试调用
# ------------------------------------------------


async def main():
    # 调用 item.create_item
    req = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "item.create_item",
            "params": {"name": "Apple", "price": 1.99},
            "id": 1,
        }
    )
    print(await server.handle_request(req))


asyncio.run(main())
