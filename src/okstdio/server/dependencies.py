"""依赖注入模块

提供轻量级的依赖注入容器，支持单例/非单例依赖管理。
"""

import threading
from typing import Annotated, Any, Callable, Dict, Tuple, Type, Optional, get_args, get_origin
from collections import defaultdict


class DependencyContainer:
    """依赖注入容器
    
    用于管理 RPC 服务器的依赖项，支持：
        - 类型键和字符串键
        - 单例/非单例生命周期管理
        - 线程安全的依赖创建
        - 运行时动态注册
    
    例子：
        ```python
        container = DependencyContainer()
        
        # 注册单例依赖
        container.register(Database, lambda: Database(), singleton=True)
        
        # 获取依赖
        db = container.get(Database)
        
        # 检查依赖是否存在
        if container.has(Database):
            print("Database is registered")
        ```
    """
    
    def __init__(self):
        """初始化依赖容器"""
        # 存储依赖注册信息：{key: (factory, singleton, instance)}
        self._dependencies: Dict[Any, Tuple[Callable, bool, Optional[Any]]] = {}
        # 线程锁，用于单例依赖的线程安全创建
        self._lock = threading.Lock()
    
    def register(
        self, 
        key: Type | str, 
        factory: Callable, 
        singleton: bool = True
    ) -> None:
        """注册依赖
        
        Args:
            key: 依赖的标识符，可以是类型或字符串
            factory: 依赖工厂函数，调用时返回依赖实例
            singleton: 是否单例，默认 True。单例依赖只会在第一次请求时创建
        
        例子：
            ```python
            # 注册类型键
            container.register(Database, lambda: Database(), singleton=True)
            
            # 注册字符串键（用于工厂函数）
            container.register("db_factory", lambda db_url: Database(db_url), singleton=False)
            ```
        """
        with self._lock:
            if singleton:
                # 单例依赖：存储工厂函数，instance 初始为 None
                self._dependencies[key] = (factory, True, None)
            else:
                # 非单例依赖：只存储工厂函数
                self._dependencies[key] = (factory, False, None)
    
    def get(self, key: Type | str) -> Any:
        """获取依赖实例
        
        Args:
            key: 依赖的标识符
        
        Returns:
            依赖实例
        
        Raises:
            KeyError: 当依赖未注册时
        
        例子：
            ```python
            # 获取类型键依赖
            db = container.get(Database)
            
            # 获取字符串键依赖
            factory = container.get("db_factory")
            db = factory("sqlite:///db.sqlite")
            ```
        """
        with self._lock:
            if key not in self._dependencies:
                raise KeyError(f"Dependency '{key}' is not registered")
            
            factory, singleton, instance = self._dependencies[key]
            
            if singleton:
                # 单例依赖：如果尚未创建实例，则创建并缓存
                if instance is None:
                    try:
                        instance = factory()
                        self._dependencies[key] = (factory, True, instance)
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to create singleton dependency '{key}': {str(e)}"
                        ) from e
                return instance
            else:
                # 非单例依赖：每次调用工厂函数创建新实例
                try:
                    return factory()
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to create dependency '{key}': {str(e)}"
                    ) from e
    
    def has(self, key: Type | str) -> bool:
        """检查依赖是否已注册
        
        Args:
            key: 依赖的标识符
        
        Returns:
            是否已注册
        
        例子：
            ```python
            if container.has(Database):
                db = container.get(Database)
            ```
        """
        return key in self._dependencies
    
    def resolve_parameter(self, param_type: Type) -> Any | None:
        """根据参数类型解析依赖
        
        按类型查找依赖，如果找到则返回实例，否则返回 None。
        支持子类匹配。
        
        Args:
            param_type: 参数类型
        
        Returns:
            依赖实例，如果未找到则返回 None
        
        例子：
            ```python
            # 假设已注册 Database 依赖
            instance = container.resolve_parameter(Database)
            
            # 如果未注册，返回 None
            instance = container.resolve_parameter(UnknownType)  # None
            ```
        """
        # 首先尝试精确匹配
        if self.has(param_type):
            return self.get(param_type)
        
        # 尝试子类匹配（遍历所有已注册的类型键）
        with self._lock:
            for key in self._dependencies.keys():
                # 只检查类型键（不是字符串键）
                if isinstance(key, type):
                    try:
                        # 检查 param_type 是否是 key 的子类
                        if issubclass(param_type, key):
                            return self.get(key)
                    except TypeError:
                        # 如果 key 不是类型，跳过
                        continue
        
        return None


class Inject:
    """标记参数为依赖注入，不出现在 API 文档中。

    配合 typing.Annotated 使用，显式声明参数由依赖容器注入，
    使其在自动生成的 API 文档和 TUI 调试器参数列表中被排除。

    用法：
        ```python
        from typing import Annotated
        from okstdio import Inject

        @app.add_method()
        def debug(device: Annotated[u2.Device, Inject()]):
            device.click()
            return {"status": "ok"}
        ```
    """
    pass


def is_inject_param(annotation: Any) -> bool:
    """检查参数注解是否为 Annotated[T, Inject()] 形式"""
    if get_origin(annotation) is Annotated:
        return any(isinstance(a, Inject) for a in get_args(annotation)[1:])
    return False


def unwrap_inject_type(annotation: Any) -> Any:
    """从 Annotated[T, Inject()] 中提取实际类型 T"""
    if get_origin(annotation) is Annotated:
        return get_args(annotation)[0]
    return annotation
