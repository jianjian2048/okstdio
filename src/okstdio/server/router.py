"""路由"""

import inspect
from typing import Dict, Callable, List, Awaitable, Any
from ..general.jsonrpc_model import JSONRPCRequest


class RPCRouter:
    """RPC 路由器"""

    def __init__(self, prefix: str):
        self.prefix = prefix
        self.methods: Dict[str, Callable] = {}
        self.middlewares: List[
            Callable[
                [JSONRPCRequest, Callable[[JSONRPCRequest], Awaitable[Any]]],
                Awaitable[Any],
            ]
        ] = []
        self.sub_routers: Dict[str, RPCRouter] = {}

    def register_middleware(self):
        """注册中间件"""

        def decorator(middleware: Callable[[dict, Callable], Awaitable[dict]]):
            self.middlewares.append(middleware)
            return middleware

        return decorator

    def register_method(self, name: str = None) -> Callable:
        """注册RPC方法"""

        def decorator(func):
            method_name = name or func.__name__
            self.methods[method_name] = func
            return func

        return decorator

    def include_router(self, router: "RPCRouter") -> None:
        """挂载子路由器"""

        if router.prefix in self.sub_routers:
            raise ValueError(f"前缀为 {router.prefix} 的路由器已存在.")
        self.sub_routers[router.prefix] = router

    def method_tree(self):
        """获取方法树, 递归获取子路由器的方法"""
        tree = self.methods
        for prefix, router in self.sub_routers.items():
            tree[prefix] = router.method_tree()
        return tree
