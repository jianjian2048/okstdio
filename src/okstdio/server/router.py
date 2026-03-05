"""路由模块

提供 RPC 路由系统的核心组件，包括路由器、方法注册和中间件管理。
"""

import inspect
from typing import Dict, Callable, List, Awaitable, Any, Tuple
from ..general.jsonrpc_model import JSONRPCRequest


class MethodsDict:
    """封装方法字典，额外记录 label

    用于存储 RPC 方法的字典，每个方法都关联一个标签（label）用于分类和文档生成。
    提供了便捷的方法来获取方法和标签信息。

    例子：
        ```python
        methods = MethodsDict()

        def my_method():
            return "Hello"

        methods["my.method"] = (my_method, "我的方法")

        # 获取方法
        func = methods.get("my.method")

        # 获取完整信息（方法和标签）
        func, label = methods.get_full("my.method")
        ```
    """

    def __init__(self):
        """初始化方法字典"""
        self._content: Dict[str, Tuple[Callable, str]] = {}

    def __setitem__(self, method_name: str, value: Tuple[Callable, str]) -> None:
        """设置方法

        Args:
            method_name: 方法名称
            value: 元组 (方法函数, 标签)
        """
        self._content[method_name] = value

    def __getitem__(self, method_name: str) -> Tuple[Callable, str]:
        """获取方法和标签

        Args:
            method_name: 方法名称

        Returns:
            Tuple[Callable, str]: (方法函数, 标签)

        Raises:
            KeyError: 当方法不存在时
        """
        return self._content[method_name]

    def __contains__(self, method_name: str) -> bool:
        """检查方法是否存在

        Args:
            method_name: 方法名称

        Returns:
            bool: 方法是否存在
        """
        return method_name in self._content

    def items(self):
        """获取所有方法项

        Returns:
            dict_items: 所有方法项的视图
        """
        return self._content.items()

    def get(self, method_name: str, default=None) -> Callable | None:
        """获取方法函数

        Args:
            method_name: 方法名称
            default: 默认值，当方法不存在时返回

        Returns:
            Callable | None: 方法函数，如果不存在则返回默认值
        """

        method = self._content.get(method_name)
        if method is None:
            return default
        return method[0]

    def get_full(self, method_name: str, default=None) -> Tuple[Callable, str] | None:
        """获取方法和标签

        Args:
            method_name: 方法名称
            default: 默认值，当方法不存在时返回

        Returns:
            Tuple[Callable, str] | None: (方法函数, 标签)，如果不存在则返回默认值
        """
        return self._content.get(method_name, default)


class MiddlewaresList:
    """封装中间件列表，保存函数与 label

    用于存储中间件的列表，每个中间件都关联一个标签（label）用于分类和文档生成。
    中间件按照添加顺序执行。

    例子：
        ```python
        middlewares = MiddlewaresList()

        async def my_middleware(request, call_next):
            print("前处理")
            result = await call_next(request)
            print("后处理")
            return result

        middlewares.append(my_middleware, "我的中间件")

        # 遍历中间件
        for middleware in middlewares:
            # 处理中间件
            pass

        # 获取完整信息（中间件和标签）
        full_list = middlewares.get_full()
        # [(middleware_func, label), ...]
        ```
    """

    def __init__(self) -> None:
        """初始化中间件列表"""
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
        """添加中间件

        Args:
            middleware: 中间件函数
            label: 中间件标签，默认 ""
        """
        self._content.append((middleware, label))

    def __iter__(self):
        """迭代中间件函数

        Returns:
            iterator: 只包含中间件函数的迭代器
        """
        return iter(self._content)

    def __len__(self) -> int:
        """获取中间件数量

        Returns:
            int: 中间件数量
        """
        return len(self._content)

    def get_full(self) -> List[Tuple[Callable, str]]:
        """获取完整信息

        Returns:
            List[Tuple[Callable, str]]: [(中间件函数, 标签), ...]
        """
        return self._content


class RPCRouter:
    """RPC 路由器

    提供路由注册和分发功能。
    支持方法注册、中间件注册和子路由器挂载。

    核心功能：
        - 注册 RPC 方法
        - 注册中间件
        - 挂载子路由器
        - 路径分发

    例子：
        ```python
        from okstdio.server import RPCRouter

        # 创建路由器
        user_router = RPCRouter("user", label="用户路由")

        # 注册方法
        @user_router.add_method(name="get", label="获取用户")
        def get_user(user_id: int) -> dict:
            return {"id": user_id}

        # 注册中间件
        @user_router.add_middleware(label="日志中间件")
        async def log_middleware(request, call_next):
            print(f"收到请求: {request.method}")
            return await call_next(request)

        # 挂载到主路由器
        main_router = RPCRouter("api")
        main_router.include_router(user_router)
        ```
    """

    def __init__(self, prefix: str, label: str = ""):
        """初始化路由器

        Args:
            prefix: 路由前缀
            label: 路由标签，默认 ""
        """
        self.prefix = prefix
        self.label = ""
        self.methods = MethodsDict()
        self.middlewares = MiddlewaresList()
        self.sub_routers: Dict[str, RPCRouter] = {}

    def add_middleware(self, label: str = "") -> Callable:
        """注册中间件装饰器

        用于注册中间件函数。中间件在请求处理前后执行。

        Args:
            label: 中间件标签，默认 ""

        Returns:
            Callable: 装饰器函数

        例子：
            ```python
            @router.add_middleware(label="请求日志")
            async def log_middleware(request, call_next):
                print(f"收到请求: {request.method}")
                result = await call_next(request)
                print(f"处理完成: {request.method}")
                return result
            ```
        """

        def decorator(middleware: Callable[[dict, Callable], Awaitable[dict]]):
            self.middlewares.append(middleware, label)
            return middleware

        return decorator

    def add_method(self, name: str = None, label: str = "") -> Callable:
        """注册 RPC 方法装饰器

        用于注册 RPC 方法。方法名称可以指定，也可以使用函数名。

        Args:
            name: 方法名称，默认为函数名
            label: 方法标签，默认 ""

        Returns:
            Callable: 装饰器函数

        例子：
            ```python
            # 使用函数名作为方法名
            @router.add_method()
            def hello(name: str) -> str:
                return f"Hello, {name}!"

            # 指定方法名
            @router.add_method(name="user.get", label="获取用户")
            def get_user(user_id: int) -> dict:
                return {"id": user_id}
            ```
        """

        def decorator(func):
            method_name = name or func.__name__
            self.methods[method_name] = (func, label)
            return func

        return decorator

    def include_router(self, router: "RPCRouter") -> None:
        """挂载子路由器

        将子路由器挂载到当前路由器下，子路由器的所有方法都会带上前缀。

        Args:
            router: 子路由器

        Raises:
            ValueError: 当子路由器前缀已存在时

        例子：
            ```python
            # 创建子路由器
            user_router = RPCRouter("user")
            @user_router.add_method()
            def get(user_id: int) -> dict:
                return {"id": user_id}

            # 挂载到主路由器
            main_router = RPCRouter("api")
            main_router.include_router(user_router)

            # 调用方式：api.user.get
            ```
        """
        if router.prefix in self.sub_routers:
            raise ValueError(f"前缀为 {router.prefix} 的路由器已存在.")
        self.sub_routers[router.prefix] = router
