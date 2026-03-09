"""okstdio - 基于 Stdio 的 JSON-RPC 父子进程通信模块

提供基于标准输入输出的 JSON-RPC 父子进程通信实现。
支持异步通信、路由分发、中间件、依赖注入和自动文档生成。

核心模块：
    - client: RPC 客户端，用于与子进程通信
    - server: RPC 服务器，用于处理父进程请求
    - general: 通用模型和错误处理

使用示例：
    ```python
    # 服务器端
    from okstdio.server import RPCServer

    app = RPCServer("my_server")

    @app.add_method()
    def hello(name: str) -> str:
        return f"Hello, {name}!"

    if __name__ == "__main__":
        app.runserver()

    # 客户端
    from okstdio.client import RPCClient

    async def main():
        async with RPCClient("my_client") as client:
            await client.start("python -m my_server")
            future = await client.send("hello", {"name": "World"})
            response = await future
            print(response.result)
    ```
"""

from .client.manager import ClientManager, BroadcastResult
from .server.dependencies import Inject

__all__ = ["ClientManager", "BroadcastResult", "Inject"]
