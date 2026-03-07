"""RPC 客户端模块

提供基于 Stdio 的 JSON-RPC 客户端实现，用于与子进程进行通信。
客户端通过标准输入输出与子进程进行 JSON-RPC 协议的消息交换。
"""

from typing import Callable, Any, Optional, Dict
from contextlib import asynccontextmanager
import asyncio
import sys
import os
import subprocess
import uuid
import json
import logging
import shutil
from pydantic import ValidationError

from ..general.jsonrpc_model import *
from ..general.errors import *
from .future import RPCFuture


class StreamListener:
    """流式监听器，支持 async for 迭代和 async with 上下文管理"""

    def __init__(self, queue: asyncio.Queue, timeout: Optional[float] = None):
        self._queue = queue
        self._timeout = timeout

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self._timeout is not None:
                msg = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
            else:
                msg = await self._queue.get()
            if msg is None:
                raise StopAsyncIteration
            return msg
        except asyncio.TimeoutError:
            raise StopAsyncIteration

    async def get(self):
        """手动获取一条消息"""
        if self._timeout is not None:
            return await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        return await self._queue.get()


class RPCClient:
    """RPC 客户端

    基于 Stdio 的 JSON-RPC 客户端，用于与子进程进行通信。
    客户端通过标准输入输出与子进程进行 JSON-RPC 协议的消息交换。

    支持的功能：
        - 异步请求/响应模式
        - 监听队列（用于接收服务器主动推送的消息）
        - 自动管理子进程生命周期
        - JSON-RPC 2.0 协议支持

    例子：
        ```python
        async def main():
            async with RPCClient("my_client") as client:
                await client.start("example.server")
                future = await client.send("healthy")
                response = await future
                print(response.model_dump_json())
        ```

    Args:
        client_name: 客户端名称，用于日志标识，默认 "rpc_client"

    Raises:
        RuntimeError: 当客户端未启动时发送请求
        RuntimeError: 当子进程启动失败时
    """

    def __init__(self, client_name: str = "rpc_client", app: Optional[str] = None, *extra_args):
        """初始化 RPC 客户端

        Args:
            client_name: 客户端名称，用于日志标识
            app: 应用程序路径，传入后 async with 会自动启动
            *extra_args: 应用程序启动参数
        """
        self._lock = asyncio.Lock()
        self._running = False
        self._read_task: Optional[asyncio.Task] = None
        self._pending_future: Dict[
            int | str, asyncio.Future[JSONRPCResponse | JSONRPCError]
        ] = {}
        self._listen_queue: Dict[
            int | str, asyncio.Queue[JSONRPCResponse | JSONRPCError]
        ] = {}

        self.client_name = client_name
        self._app = app
        self._extra_args = extra_args
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logger = logging.getLogger(self.client_name)

    def add_listen_queue(self, listen_id: int | str):
        """添加监听队列

        用于接收服务器主动推送的消息。当收到的消息 ID 匹配监听队列 ID 时，
        消息会被推入对应的队列中。

        Args:
            listen_id: 监听队列的 ID

        Returns:
            asyncio.Queue: 创建的监听队列，如果已存在则返回现有队列
        """
        if self._listen_queue.get(listen_id):
            return
        self._listen_queue[listen_id] = asyncio.Queue()
        return self._listen_queue[listen_id]

    def get_listen_queue(self, listen_id: int | str):
        """获取监听队列

        Args:
            listen_id: 监听队列的 ID

        Returns:
            asyncio.Queue | None: 监听队列，如果不存在则返回 None
        """
        if not self._listen_queue.get(listen_id):
            return None
        return self._listen_queue[listen_id]

    def del_listen_queue(self, listen_id: int | str):
        """删除监听队列

        Args:
            listen_id: 监听队列的 ID
        """
        self._listen_queue.pop(listen_id, None)

    async def get_server_methods(self) -> dict:
        """获取服务器方法树

        通过调用服务器的 __system__ 方法获取完整的方法树结构。

        Returns:
            dict: 服务器方法树字典，包含：
                - server_name: 服务器名称
                - version: 服务器版本
                - label: 服务器标签
                - methods: 方法列表
                - middlewares: 中间件列表
                - routers: 路由器字典

        Raises:
            RuntimeError: 当客户端未启动时

        例子：
            ```python
            async with RPCClient("my_client") as client:
                await client.start("example.server")

                # 获取服务器方法树
                method_tree = await client.get_server_methods()

                # 列出所有方法
                for method in method_tree["methods"]:
                    print(f"方法：{method['name']}, 路径：{method['path']}")

                # 查看路由
                for router_name, router_info in method_tree["routers"].items():
                    print(f"路由：{router_name}, 方法数：{len(router_info['methods'])}")
            ```
        """
        future = await self.send("__system__")
        response = await future
        return response.result

    async def read_loop(self):
        """读循环

        持续从子进程的标准输出读取 JSON-RPC 响应消息。
        根据消息 ID 将响应分发到对应的 Future 或监听队列。

        循环会在以下情况停止：
            - 子进程关闭输出流
            - 发生未处理的异常
        """
        while self._running:

            try:
                # 读取消息
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=1.0
                )

                if not response_line:
                    self.logger.debug("连接已断开")
                    break

                try:
                    response_text = response_line.decode("utf-8").strip()
                    self.logger.debug(response_text)
                except UnicodeDecodeError as e:
                    self.logger.warning(f"解码错误，跳过此行: {e}")
                    continue

                if not response_text:
                    continue

                try:
                    response = json.loads(response_text)
                    response_id = response.get("id")
                    if not response_id:
                        continue

                    if response.get("result"):
                        response = JSONRPCResponse.model_validate(response)
                    elif response.get("error"):
                        response = JSONRPCError.model_validate(response)

                    # 如果是监听队列需要的响应,则将结果推入队列
                    if response_id in self._listen_queue.keys():
                        await self._listen_queue[response_id].put(response)
                        continue

                    future = self._pending_future.pop(response_id, None)
                    # 防止 future 已被取消.
                    if not future:
                        continue
                    future.set_result(response)

                except json.JSONDecodeError as e:
                    self.logger.error(f"解析消息失败: {e}")
                except ValidationError as e:
                    self.logger.error(f"响应校验错误 {e.errors(include_url=False)}")
                except Exception as e:
                    self.logger.error(f"处理消息时出错: {e}")

            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                self.logger.exception(f"READ 触发未处理异常: {e}")
                break
                

    async def send(
        self,
        method: str,
        params: Any = {},
        request_id: int | str | None = None,
    ) -> asyncio.Future:
        """发送 JSON-RPC 请求并等待响应

        发送请求后返回一个 Future 对象，可以通过 await 等待响应。

        Args:
            method: 要调用的 RPC 方法名称
            params: 方法参数，默认为空字典
            request_id: 请求 ID，如果未提供则自动生成 UUID

        Returns:
            asyncio.Future: 用于等待响应的 Future 对象

        Raises:
            RuntimeError: 当客户端未启动时

        例子：
            ```python
            future = await client.send("hero.create", {"hero": {"hero_name": "张三"}})
            response = await future
            print(response.result)
            ```
        """
        if not self._running:
            raise RuntimeError("子进程未启动")

        async with self._lock:

            if request_id is None:
                request_id = uuid.uuid1().hex

            # 创建等待响应的 Future
            future = asyncio.get_event_loop().create_future()
            self._pending_future[request_id] = future

            # 发送请求
            request = JSONRPCRequest(id=request_id, method=method, params=params)

            self.process.stdin.write(request.encode("utf-8") + b"\n")
            await self.process.stdin.drain()

            return future

    async def start(self, app: Optional[str] = None, *extra_args) -> None:
        """启动子进程

        根据提供的应用路径自动判断启动方式：
            - 模块引用（如 "example.server"）：使用 `python -m` 启动
            - Python 脚本（如 "server.py"）：直接执行
            - 可执行文件：直接执行

        Args:
            app: 应用程序路径，可以是模块名、脚本路径或可执行文件
            *extra_args: 应用程序启动参数

        Raises:
            RuntimeError: 当子进程启动失败时

        例子：
            ```python
            # 启动模块
            await client.start("example.server")

            # 启动脚本
            await client.start("path/to/server.py")

            # 启动可执行文件
            await client.start("./my_server")

            # 传递额外参数
            await client.start("example.server", "--port", "8080")
            ```
        """

        app = app or self._app
        if app is None:
            raise RuntimeError("未指定应用程序路径，请在构造时或 start() 时传入 app 参数")
        extra_args = extra_args or self._extra_args

        def _is_module_ref(app: str) -> bool:
            """判断是否python模块"""
            return "." in app and not app.endswith(".py")

        def _is_script(app: str) -> bool:
            """判断是否python脚本"""
            return app.endswith(".py") and os.path.exists(app)

        def _is_executable(app: str) -> bool:
            """判断是否可执行文件"""
            if os.path.isabs(app) and os.access(app, os.X_OK):
                return True
            return shutil.which(app) is not None

        try:
            creationflags = 0
            if _is_module_ref(app):
                cmd = [sys.executable, "-m", app, *extra_args]
            elif _is_script(app):
                cmd = [sys.executable, app, *extra_args]
            elif _is_executable(app):
                cmd = [app, *extra_args]
                if os.name == "nt":
                    creationflags = subprocess.CREATE_NO_WINDOW
            else:
                cmd = [sys.executable, "-m", app, *extra_args]

            # 设置环境变量强制使用 UTF-8 编码
            env = os.environ.copy()
            if os.name == "nt":
                env["PYTHONIOENCODING"] = "utf-8"

            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=creationflags,
                env=env,
            )

            # 等待子进程启动
            await asyncio.sleep(1)

            if self.process.returncode is not None:
                stderr_data = await self.process.stderr.read()
                error_msg = "未知错误"
                if stderr_data:
                    for encoding in ["utf-8", "gbk", "cp936", "latin-1"]:
                        try:
                            error_msg = stderr_data.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                raise RuntimeError(f"子进程启动失败: {error_msg}")

            self._running = True
            self._read_task = asyncio.create_task(self.read_loop())

        except Exception as e:
            raise e

    async def stop(self) -> None:
        """停止客户端

        停止读循环、关闭子进程、清理资源。
        该方法是异步安全的，可以安全地在协程中调用。

        清理的资源：
            - 取消读循环任务
            - 关闭子进程
            - 清理待处理的 Future
            - 清理监听队列
        """
        # 停止读循环
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        # 关闭子进程
        if self.process:
            self.process.stdin.close()
            try:
                await self.process.stdin.wait_closed()
            except Exception:
                pass
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()

        # 清理未完成的 future
        for future in self._pending_future.values():
            future.cancel()
        self._pending_future.clear()

        self.process = None
        self._read_task = None
        self._pending_future = {}
        self._listen_queue = {}

    async def __aenter__(self):
        """异步上下文管理器进入，如果构造时传入了 app 则自动启动"""
        if self._app and not self._running:
            await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.stop()

    def call(self, method: str, params: Any = None, *, request_id: Optional[str] = None, timeout: Optional[float] = None) -> RPCFuture:
        """发送请求并返回可链式调用的 RPCFuture

        同步方法，使得 `await client.call("method").then(handler)` 可以自然书写。

        Args:
            method: 要调用的 RPC 方法名称
            params: 方法参数，默认为空字典
            request_id: 请求 ID，如果未提供则自动生成 UUID
            timeout: 超时时间（秒）

        Returns:
            RPCFuture: 可链式调用的 Future 对象

        Raises:
            RuntimeError: 当客户端未启动时
        """
        if not self._running:
            raise RuntimeError("子进程未启动")
        if request_id is None:
            request_id = uuid.uuid1().hex

        future = asyncio.get_running_loop().create_future()
        self._pending_future[request_id] = future

        request = JSONRPCRequest(id=request_id, method=method, params=params or {})
        asyncio.create_task(self._do_send(request))

        return RPCFuture(future, timeout=timeout)

    async def _do_send(self, request: JSONRPCRequest):
        """内部发送方法，通过 stdin 写入请求"""
        async with self._lock:
            self.process.stdin.write(request.encode("utf-8") + b"\n")
            await self.process.stdin.drain()

    @asynccontextmanager
    async def stream(self, listen_id: int | str, *, timeout: Optional[float] = None):
        """流式推送上下文管理器

        自动管理监听队列的生命周期。

        Args:
            listen_id: 监听队列 ID
            timeout: 每条消息的超时时间（秒）

        例子：
            ```python
            async with client.stream(task_id) as listener:
                async for msg in listener:
                    print(msg.result)
            ```
        """
        queue = self.add_listen_queue(listen_id)
        try:
            yield StreamListener(queue, timeout)
        finally:
            self.del_listen_queue(listen_id)
