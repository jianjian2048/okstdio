from typing import Callable, Any, Optional, Dict
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


class RPCClient:

    def __init__(self, client_name: str = "rpc_client"):
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
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logger = logging.getLogger(self.client_name)

    def add_listen_queue(self, listen_id: int | str):
        if self._listen_queue.get(listen_id):
            return
        self._listen_queue[listen_id] = asyncio.Queue()

    def del_listen_queue(self, listen_id: int | str):
        self._listen_queue.pop(listen_id, None)

    async def read_loop(self):
        """读循环"""

        while self._running:

            try:
                # 读取消息
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=1.0
                )
                if not response_line:
                    self.logger.debug("连接已断开")
                    break

                response_text = response_line.decode("utf-8").strip()
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
        request_id: int | str = None,
    ) -> asyncio.Future:
        """发送请求并等待响应"""
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

    async def start(self, app: str, *extra_args) -> None:
        """启动应用程序
        Args:
            app: 应用程序路径
            *args: 应用程序启动参数
        """

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

            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=creationflags,
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
        """停止"""

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
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
