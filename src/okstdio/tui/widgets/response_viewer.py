"""响应查看器组件

显示 JSON-RPC 响应和日志的 TabbedContent 组件。
"""

import json
from datetime import datetime
from typing import Any
from textual.widgets import TabbedContent, TabPane, Static, RichLog
from textual.containers import Vertical, VerticalScroll
from textual.message import Message


def format_json(data: Any, indent: int = 2) -> str:
    """格式化 JSON 数据

    Args:
        data: 要格式化的数据
        indent: 缩进空格数

    Returns:
        str: 格式化后的 JSON 字符串
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


class JsonResponseViewer(VerticalScroll):
    """JSON 响应查看器

    以格式化的方式显示 JSON 响应。
    """

    def __init__(self, **kwargs) -> None:
        """初始化 JSON 查看器"""
        super().__init__(**kwargs)
        self._current_response: Any = None

    def compose(self):
        """创建子组件"""
        yield Static(id="json-content", expand=True)

    def show_response(self, response: Any) -> None:
        """显示响应

        Args:
            response: 响应数据
        """
        self._current_response = response

        # 格式化 JSON
        formatted = format_json(response)

        # 更新显示
        content = self.query_one("#json-content", Static)
        content.update(formatted)

    def clear(self) -> None:
        """清空显示"""
        self._current_response = None
        content = self.query_one("#json-content", Static)
        content.update("[dim]等待响应...[/dim]")


class ResponseViewer(Vertical):
    """响应查看器

    包含 Response 和 Log 两个标签页。

    例子:
        ```python
        viewer = ResponseViewer()
        viewer.show_response(response)
        viewer.log_request("hello", {"name": "test"}, response)
        ```
    """

    def __init__(self, **kwargs) -> None:
        """初始化响应查看器"""
        super().__init__(**kwargs)

    def compose(self):
        """创建子组件"""
        with TabbedContent(id="tabbed-content"):
            with TabPane("Response", id="tab-response"):
                yield JsonResponseViewer(id="json-viewer")
            with TabPane("Log", id="tab-log"):
                yield RichLog(id="request-log", wrap=True, highlight=True)

    def on_mount(self) -> None:
        """挂载后初始化"""
        # 初始化显示
        json_viewer = self.query_one("#json-viewer", JsonResponseViewer)
        json_viewer.clear()

        # 初始化日志
        log = self.query_one("#request-log", RichLog)
        log.write("[dim]请求日志将显示在这里...[/dim]")

    def show_response(self, response: Any) -> None:
        """显示响应

        Args:
            response: 响应数据（JSONRPCResponse 或 dict）
        """
        # 显示响应
        json_viewer = self.query_one("#json-viewer", JsonResponseViewer)

        if hasattr(response, "model_dump"):
            # Pydantic 模型
            json_viewer.show_response(response.model_dump())
        elif isinstance(response, dict):
            json_viewer.show_response(response)
        else:
            json_viewer.show_response(str(response))

    def log_request(
        self,
        method: str,
        params: dict[str, Any],
        response: Any,
        error: bool = False
    ) -> None:
        """记录请求日志

        Args:
            method: 方法名
            params: 请求参数
            response: 响应数据
            error: 是否为错误响应
        """
        log = self.query_one("#request-log", RichLog)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 请求日志
        if error:
            log.write(f"[red]✗ {timestamp}[/red] [bold]{method}[/bold]")
        else:
            log.write(f"[green]✓ {timestamp}[/green] [bold]{method}[/bold]")

        # 参数
        log.write(f"  [dim]Params:[/dim] {format_json(params)}")

        # 响应
        if hasattr(response, "model_dump"):
            resp_data = response.model_dump()
        elif isinstance(response, dict):
            resp_data = response
        else:
            resp_data = str(response)

        if error:
            log.write(f"  [dim]Error:[/dim] [red]{format_json(resp_data)}[/red]")
        else:
            log.write(f"  [dim]Result:[/dim] {format_json(resp_data.get('result', resp_data))}")

        log.write("")  # 空行分隔

    def log_message(self, message: str, style: str = "") -> None:
        """记录普通日志消息

        Args:
            message: 日志消息
            style: 样式字符串
        """
        log = self.query_one("#request-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if style:
            log.write(f"[{timestamp}] [{style}]{message}[/{style}]")
        else:
            log.write(f"[{timestamp}] {message}")

    def clear_log(self) -> None:
        """清空日志"""
        log = self.query_one("#request-log", RichLog)
        log.clear()

    def clear_response(self) -> None:
        """清空响应"""
        json_viewer = self.query_one("#json-viewer", JsonResponseViewer)
        json_viewer.clear()
