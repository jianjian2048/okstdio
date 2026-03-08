"""ClientManager 批量客户端管理器

提供批量管理多个 RPCClient 的能力，支持统一的生命周期管理和请求分发。
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
import asyncio

from .application import RPCClient


@dataclass
class BroadcastResult:
    """广播结果封装"""
    client_name: str
    result: Any = None
    response: Any = None
    error: Optional[Exception] = None


class ClientManager:
    """批量客户端管理器

    统一管理多个 RPCClient 的生命周期和请求分发。

    例子：
        ```python
        async with ClientManager() as manager:
            manager.add("server1", "tests.test_server")
            manager.add("server2", "tests.test_server")
            await manager.start_all()
            results = await manager.broadcast("healthy")
            for r in results:
                print(f"{r.client_name}: {r.result}")
        ```
    """

    def __init__(self):
        self._clients: Dict[str, RPCClient] = {}

    def add(self, client_name: str, app: str, *extra_args) -> RPCClient:
        """创建并添加客户端

        Args:
            client_name: 客户端名称
            app: 应用程序路径
            *extra_args: 应用程序启动参数

        Returns:
            RPCClient: 创建的客户端实例
        """
        client = RPCClient(client_name, app=app, *extra_args)
        self._clients[client_name] = client
        return client

    def add_client(self, client: RPCClient) -> None:
        """添加已有的客户端实例

        Args:
            client: RPCClient 实例
        """
        self._clients[client.client_name] = client

    def remove(self, client_name: str) -> Optional[RPCClient]:
        """移除客户端（不停止）

        Args:
            client_name: 客户端名称

        Returns:
            移除的客户端实例，不存在则返回 None
        """
        return self._clients.pop(client_name, None)

    async def remove_and_stop(self, client_name: str) -> None:
        """移除并停止客户端

        Args:
            client_name: 客户端名称
        """
        client = self._clients.pop(client_name, None)
        if client:
            await client.stop()

    def get(self, client_name: str) -> Optional[RPCClient]:
        """获取客户端

        Args:
            client_name: 客户端名称

        Returns:
            RPCClient 实例，不存在则返回 None
        """
        return self._clients.get(client_name)

    def __getitem__(self, client_name: str) -> RPCClient:
        return self._clients[client_name]

    def __contains__(self, client_name: str) -> bool:
        return client_name in self._clients

    def __len__(self) -> int:
        return len(self._clients)

    @property
    def clients(self) -> Dict[str, RPCClient]:
        """返回所有客户端字典"""
        return dict(self._clients)

    @property
    def client_names(self) -> List[str]:
        """返回所有客户端名称"""
        return list(self._clients.keys())

    async def start_all(self) -> None:
        """并发启动所有客户端

        Raises:
            RuntimeError: 当有客户端启动失败时，包含失败详情
        """
        tasks = {
            name: asyncio.create_task(client.start())
            for name, client in self._clients.items()
        }
        await asyncio.gather(*tasks.values(), return_exceptions=True)

        failures = {}
        for name, task in tasks.items():
            exc = task.exception() if not task.cancelled() else None
            if exc:
                failures[name] = exc

        if failures:
            details = "; ".join(f"{name}: {exc}" for name, exc in failures.items())
            raise RuntimeError(f"部分客户端启动失败: {details}")

    async def stop_all(self) -> None:
        """并发停止所有客户端，静默忽略异常"""
        tasks = [
            asyncio.create_task(client.stop())
            for client in self._clients.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to(self, client_name: str, method: str, params: Any = {}) -> asyncio.Future:
        """向指定客户端发送请求

        Args:
            client_name: 客户端名称
            method: RPC 方法名
            params: 方法参数

        Returns:
            asyncio.Future: 用于等待响应的 Future

        Raises:
            KeyError: 客户端不存在
        """
        client = self._clients[client_name]
        return await client.send(method, params)

    def call_to(self, client_name: str, method: str, params: Any = None, *, timeout: Optional[float] = None):
        """向指定客户端发送请求（链式调用风格）

        Args:
            client_name: 客户端名称
            method: RPC 方法名
            params: 方法参数
            timeout: 超时时间（秒）

        Returns:
            RPCFuture: 可链式调用的 Future

        Raises:
            KeyError: 客户端不存在
        """
        client = self._clients[client_name]
        return client.call(method, params, timeout=timeout)

    async def broadcast(
        self,
        method: str,
        params: Any = {},
        *,
        targets: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> List[BroadcastResult]:
        """广播请求到多个客户端

        不抛异常，每个结果独立封装到 BroadcastResult。

        Args:
            method: RPC 方法名
            params: 方法参数
            targets: 目标客户端名称列表，None 表示所有客户端
            timeout: 每个请求的超时时间（秒）

        Returns:
            List[BroadcastResult]: 广播结果列表
        """
        target_names = targets or list(self._clients.keys())
        target_clients = {
            name: self._clients[name]
            for name in target_names
            if name in self._clients
        }

        async def _send_one(name: str, client: RPCClient) -> BroadcastResult:
            try:
                future = await client.send(method, params)
                if timeout is not None:
                    response = await asyncio.wait_for(future, timeout=timeout)
                else:
                    response = await future
                return BroadcastResult(
                    client_name=name,
                    result=response.result if hasattr(response, 'result') else None,
                    response=response,
                )
            except Exception as e:
                return BroadcastResult(client_name=name, error=e)

        tasks = [_send_one(name, client) for name, client in target_clients.items()]
        return await asyncio.gather(*tasks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_all()
