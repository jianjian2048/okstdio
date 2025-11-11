"""路由"""

import inspect
from typing import Dict, Callable, List, Awaitable, Any, Tuple
from ..general.jsonrpc_model import JSONRPCRequest


# region 封装方法字典
class MethodsDict:
    """封装方法字典，额外记录 label"""

    def __init__(self):
        self._content: Dict[str, Tuple[Callable, str]] = {}

    def __setitem__(self, method_name: str, value: Tuple[Callable, str]) -> None:
        self._content[method_name] = value

    def __getitem__(self, method_name: str) -> Tuple[Callable, str]:
        return self._content[method_name]

    def __contains__(self, method_name: str) -> bool:
        return method_name in self._content

    def items(self):
        return self._content.items()

    def get(self, method_name: str, default=None) -> Callable | None:
        return (
            self._content.get(method_name, default)[0]
            if method_name in self._content
            else default
        )

    def get_full(self, method_name: str, default=None) -> Tuple[Callable, str] | None:
        return self._content.get(method_name, default)


# region 封装中间件列表
class MiddlewaresList:
    """封装中间件列表，保存函数与 label"""

    def __init__(self) -> None:
        self._content: List[
            Tuple[
                Callable[
                    [JSONRPCRequest, Callable[[JSONRPCRequest], Awaitable[Any]]],
                    Awaitable[Any],
                ],
                str,
            ]
        ] = []

    def append(
        self,
        middleware: Callable[
            [JSONRPCRequest, Callable[[JSONRPCRequest], Awaitable[Any]]], Awaitable[Any]
        ],
        label: str = "",
    ) -> None:
        self._content.append((middleware, label))

    def __iter__(self):
        return iter(self._content)

    def __len__(self) -> int:
        return len(self._content)

    def __iter__(self):
        return iter([func for func, label in self._content])

    def get_full(self) -> List[Tuple[Callable, str]]:
        return self._content


# region RPC路由器
class RPCRouter:
    """RPC 路由器"""

    def __init__(self, prefix: str, label: str = ""):
        self.prefix = prefix
        self.label = ""
        self.methods = MethodsDict()
        self.middlewares = MiddlewaresList()
        self.sub_routers: Dict[str, RPCRouter] = {}

    def add_middleware(self, label: str = "") -> Callable:
        """注册中间件"""

        def decorator(middleware: Callable[[dict, Callable], Awaitable[dict]]):
            self.middlewares.append(middleware, label)
            return middleware

        return decorator

    def add_method(self, name: str = None, label: str = "") -> Callable:
        """注册RPC方法"""

        def decorator(func):
            method_name = name or func.__name__
            self.methods[method_name] = (func, label)
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
