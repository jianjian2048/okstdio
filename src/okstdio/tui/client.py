"""TUI 专用客户端

继承 RPCClient，拦截所有 I/O 消息用于调试显示。
"""

import json
import asyncio
from typing import Callable, Optional, Any

from pydantic import ValidationError

from ..client import RPCClient
from ..general.jsonrpc_model import JSONRPCRequest, JSONRPCResponse, JSONRPCError


class TUIClient(RPCClient):
    """TUI 专用客户端，拦截所有 I/O 用于调试显示

    通过回调钩子在消息收发时通知 TUI 层，实现：
    - 记录所有发送的请求
    - 记录所有接收的响应
    - 捕获未匹配的服务器主动推送
    """

    def __init__(
        self,
        client_name: str = "rcptui",
        on_send: Optional[Callable[[str, Any, str], None]] = None,
        on_recv: Optional[Callable[[dict], None]] = None,
        on_push: Optional[Callable[[Any, Any], None]] = None,
    ):
        super().__init__(client_name)
        self._on_send = on_send
        self._on_recv = on_recv
        self._on_push = on_push

    async def read_loop(self):
        """重写读循环，在消息分发前通过回调通知 TUI"""
        while self._running:
            try:
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

                    # 钩子：记录所有接收的原始消息
                    if self._on_recv:
                        self._on_recv(response)

                    if response.get("result"):
                        parsed = JSONRPCResponse.model_validate(response)
                    elif response.get("error"):
                        parsed = JSONRPCError.model_validate(response)
                    else:
                        continue

                    # 匹配监听队列
                    if response_id in self._listen_queue.keys():
                        await self._listen_queue[response_id].put(parsed)
                        continue

                    # 匹配 pending future
                    future = self._pending_future.pop(response_id, None)
                    if future:
                        future.set_result(parsed)
                        continue

                    # 未匹配 → 服务器主动推送
                    if self._on_push:
                        self._on_push(response_id, parsed)

                except json.JSONDecodeError as e:
                    self.logger.error(f"解析消息失败: {e}")
                except ValidationError as e:
                    self.logger.error(f"响应校验错误 {e.errors(include_url=False)}")
                except Exception as e:
                    self.logger.error(f"处理消息时出错: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.exception(f"READ 触发未处理异常: {e}")
                break

    async def _do_send(self, request: JSONRPCRequest):
        """重写发送方法，在发送前触发 on_send 回调"""
        if self._on_send:
            self._on_send(request.method, request.params, request.id)
        await super()._do_send(request)
