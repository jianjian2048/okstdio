"""Okstdio TUI 调试工具主应用

提供 JSON-RPC 服务器的可视化和调试功能。
"""

import asyncio
import json
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive
from textual import work

from ..client import RPCClient
from ..general.errors import RPCError
from .widgets import MethodTreeWidget, ParamsEditor, ResponseViewer


class MethodTreeContainer(Vertical):
    """方法树容器"""


class RightContainer(Vertical):
    """右侧容器"""


class AppMainContainer(Horizontal):
    """应用主容器"""


class OkstdioApp(App):
    """Okstdio 调试工具应用

    基于 Stdio 的 JSON-RPC 调试工具，支持：
        - 可视化方法树浏览
        - 参数编辑和请求发送
        - 响应查看和日志记录

    快捷键:
        Ctrl+j: 发送请求
        Ctrl+r: 重启服务器
        Ctrl+q: 退出

    Args:
        server_path: 服务器路径，可以是模块名或脚本路径
    """

    CSS_PATH = "oktui.scss"

    BINDINGS = [
        Binding("ctrl+j", "send_request", "发送请求", show=True),
        Binding("ctrl+r", "restart_server", "重启服务", show=True),
        Binding("ctrl+l", "clear_log", "清理日志", show=True),
        Binding("ctrl+q", "quit", "退出", show=True),
    ]

    # 响应式状态
    server_path: reactive[str] = reactive("")
    selected_method: reactive[dict | None] = reactive(None)

    def __init__(self, server_path: str = "", **kwargs) -> None:
        """初始化应用

        Args:
            server_path: 服务器路径
            **kwargs: 传递给 App 的其他参数
        """
        super().__init__(**kwargs)
        self.server_path = server_path
        self._client: Optional[RPCClient] = None
        self._method_tree: dict[str, Any] = {}
        self._connecting = False

    def compose(self) -> ComposeResult:
        """创建应用布局"""
        yield Header()
        with AppMainContainer():
            with MethodTreeContainer():
                yield MethodTreeWidget("Server", id="method-tree")
            with RightContainer():
                yield ParamsEditor(id="params-editor")
                yield ResponseViewer(id="response-viewer")
        yield Footer()

    async def on_mount(self) -> None:
        """挂载后自动连接服务器"""
        if self.server_path:
            self._connect_server()

    async def on_unmount(self) -> None:
        """卸载时清理资源"""
        await self._disconnect_server()

    @work(exclusive=True, name="connect_server")
    async def _connect_server(self) -> None:
        """连接服务器（在 worker 中运行，不阻塞 UI）"""
        if self._connecting:
            return

        self._connecting = True
        viewer = self.query_one("#response-viewer", ResponseViewer)
        viewer.log_message(f"正在连接服务器: {self.server_path}", "yellow")

        try:
            await self._disconnect_server()

            self._client = RPCClient("rcptui")
            await self._client.start(self.server_path)
            self._method_tree = await self._client.get_server_methods()

            tree = self.query_one("#method-tree", MethodTreeWidget)
            tree.update_tree(self._method_tree)

            viewer.log_message(
                f"服务器已连接: {self._method_tree.get('server_name', 'unknown')} "
                f"[{self._method_tree.get('version', '')}]",
                "green"
            )

        except Exception as e:
            viewer.log_message(f"连接失败: {str(e)}", "red")
            self._client = None

        finally:
            self._connecting = False

    async def _disconnect_server(self) -> None:
        """断开服务器连接"""
        if self._client:
            try:
                await self._client.stop()
            except Exception:
                pass
            self._client = None

    def on_method_tree_widget_method_selected(
        self,
        event: MethodTreeWidget.MethodSelected
    ) -> None:
        """方法选中事件处理

        Args:
            event: 方法选中事件
        """
        self.selected_method = event.method_info

        # 更新参数编辑器
        editor = self.query_one("#params-editor", ParamsEditor)
        editor.set_method(
            method_name=event.method_info.get("path", ""),
            method_label=event.method_info.get("label", ""),
            params=event.method_info.get("params", [])
        )

    async def action_send_request(self) -> None:
        """发送请求动作"""
        if not self.selected_method:
            self.notify("请先选择一个方法", severity="warning")
            return

        if not self._client:
            self.notify("服务器未连接", severity="error")
            return

        editor = self.query_one("#params-editor", ParamsEditor)

        try:
            params = editor.get_params()
        except json.JSONDecodeError as e:
            self.notify(f"JSON 格式错误: {e}", severity="error")
            return

        self._do_send_request(self.selected_method.get("path", ""), params)

    @work(exclusive=True, name="send_request")
    async def _do_send_request(self, method_path: str, params: dict) -> None:
        """执行请求发送（在 worker 中运行，不阻塞 UI）"""
        viewer = self.query_one("#response-viewer", ResponseViewer)
        viewer.log_message(f"发送请求: {method_path}")

        try:
            response = await self._client.call(method_path, params).then(
                lambda response: response
            )
            viewer.show_response(response)
            viewer.log_request(method_path, params, response)
            self.notify("请求成功")

        except RPCError as e:
            viewer.show_error(e)
            viewer.log_error(method_path, params, e)
            self.notify(f"[{e.code}] {e.message}", severity="warning")

        except Exception as e:
            viewer.log_message(f"请求失败: {str(e)}", "red")
            self.notify(f"请求失败: {e}", severity="error")

    def action_clear_log(self) -> None:
        """清理日志"""
        viewer = self.query_one("#response-viewer", ResponseViewer)
        viewer.clear_log()
        self.notify("日志已清理")

    async def action_restart_server(self) -> None:
        """重启服务器动作"""
        if not self.server_path:
            self.notify("未指定服务器路径", severity="warning")
            return

        self.notify("正在重启服务器...")
        self._connect_server()
