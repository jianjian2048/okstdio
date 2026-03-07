"""响应查看器组件

显示 JSON-RPC 响应和日志。
Response 面板使用 TextArea（可复制），Log 面板使用 RichLog（富文本格式）。
"""

import json
from datetime import datetime
from typing import Any
from textual.widgets import TabbedContent, TabPane, TextArea, RichLog
from textual.containers import Vertical


def format_json(data: Any, indent: int = 2) -> str:
    """格式化 JSON 数据"""
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


def format_json_inline(data: Any) -> str:
    """单行格式化 JSON 数据"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


class ResponseViewer(Vertical):
    """响应查看器

    包含 Response（TextArea）和 Log（RichLog）两个标签页。
    日志按行输出请求、结果和监听队列推送消息。
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self):
        with TabbedContent(id="tabbed-content"):
            with TabPane("Response", id="tab-response"):
                yield TextArea(
                    "",
                    id="response-text",
                    language="json",
                    read_only=True,
                    soft_wrap=True,
                )
            with TabPane("Log", id="tab-log"):
                yield RichLog(id="request-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        response_text = self.query_one("#response-text", TextArea)
        response_text.placeholder = "响应窗口"

    def show_response(self, response: Any) -> None:
        """显示响应到 Response 面板"""
        text_area = self.query_one("#response-text", TextArea)
        if hasattr(response, "model_dump"):
            text_area.text = format_json(response.model_dump())
        elif isinstance(response, dict):
            text_area.text = format_json(response)
        else:
            text_area.text = str(response)

    def show_error(self, error: Any) -> None:
        """显示 RPC 错误到 Response 面板"""
        text_area = self.query_one("#response-text", TextArea)
        error_data: dict[str, Any] = {
            "code": error.code,
            "message": error.message,
        }
        if error.data:
            error_data["data"] = error.data
        text_area.text = format_json({"error": error_data})

    # ---- Log 面板：按行输出请求、结果、推送 ----

    def log_request(
        self, method: str, params: dict[str, Any], response: Any
    ) -> None:
        """记录完整的请求-响应日志（按行输出）"""
        log = self.query_one("#request-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 请求行
        log.write(f"[bold cyan]REQ[/bold cyan]  {ts} [bold]{method}[/bold]  {format_json_inline(params)}")

        # 结果行
        if hasattr(response, "model_dump"):
            resp_data = response.model_dump()
        elif isinstance(response, dict):
            resp_data = response
        else:
            resp_data = str(response)

        result = resp_data.get("result", resp_data) if isinstance(resp_data, dict) else resp_data
        log.write(f"[bold green]RES[/bold green]  {ts} [bold]{method}[/bold]  {format_json_inline(result)}")

    def log_error(
        self, method: str, params: dict[str, Any], error: Any
    ) -> None:
        """记录错误请求日志（按行输出）"""
        log = self.query_one("#request-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 请求行
        log.write(f"[bold cyan]REQ[/bold cyan]  {ts} [bold]{method}[/bold]  {format_json_inline(params)}")

        # 错误行
        error_info = f"\\[{error.code}] {error.message}"
        if error.data:
            error_info += f"  {format_json_inline(error.data)}"
        log.write(f"[bold red]ERR[/bold red]  {ts} [bold]{method}[/bold]  {error_info}")

    def log_push(self, listen_id: int | str, data: Any) -> None:
        """记录监听队列推送消息"""
        log = self.query_one("#request-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log.write(f"[bold yellow]PUSH[/bold yellow] {ts} [dim]id={listen_id}[/dim]  {format_json_inline(data)}")

    def log_message(self, message: str, style: str = "") -> None:
        """记录普通日志消息"""
        log = self.query_one("#request-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if style:
            log.write(f"[bold blue]INFO[/bold blue] {ts} [{style}]{message}[/{style}]")
        else:
            log.write(f"[bold blue]INFO[/bold blue] {ts} {message}")

    def clear_log(self) -> None:
        """清空日志"""
        log = self.query_one("#request-log", RichLog)
        log.clear()

    def clear_response(self) -> None:
        """清空响应"""
        text_area = self.query_one("#response-text", TextArea)
        text_area.text = ""
