"""Okstdio TUI 模块

提供 JSON-RPC 调试工具的 TUI 界面。
"""

import argparse

from .app import OkstdioApp

__all__ = ["OkstdioApp", "run_app"]


def run_app() -> None:
    """命令行入口函数

    启动 Okstdio 调试工具。

    用法:
        rcptui --server "tests.test_server"
        rcptui --server "path/to/server.py"
    """
    parser = argparse.ArgumentParser(
        prog="rcptui",
        description="Okstdio JSON-RPC 调试工具"
    )
    parser.add_argument(
        "--server",
        required=True,
        help="服务器路径（模块名或脚本路径）"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    app = OkstdioApp(server_path=args.server)
    app.run()