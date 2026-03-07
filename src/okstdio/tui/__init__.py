"""Okstdio TUI 模块

提供 JSON-RPC 调试工具的 TUI 界面。
"""

import argparse

__all__ = ["OkstdioApp", "run_app"]


def __getattr__(name: str):
    if name == "OkstdioApp":
        from .app import OkstdioApp

        return OkstdioApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def run_app() -> None:
    """命令行入口函数

    启动 Okstdio 调试工具。

    用法:
        rcptui --server "tests.test_server"
        rcptui --server "path/to/server.py"
    """
    try:
        from .app import OkstdioApp
    except ImportError:
        print("错误：TUI 调试工具需要安装 textual 依赖。")
        print("请运行：pip install okstdio[tui]")
        raise SystemExit(1)

    parser = argparse.ArgumentParser(
        prog="rcptui", description="Okstdio JSON-RPC 调试工具"
    )
    parser.add_argument(
        "--server", required=True, help="服务器路径（模块名或脚本路径）"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    app = OkstdioApp(server_path=args.server)
    app.run()
