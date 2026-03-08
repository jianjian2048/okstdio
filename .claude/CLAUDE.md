# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

okstdio-enhance 是一个基于 Stdio 的 JSON-RPC 父子进程通信框架，实现了 JSON-RPC 2.0 协议规范。

## 常用命令

```bash
# 安装依赖
uv sync

# 安装含 TUI 支持
uv sync --extra tui

# 构建包
uv build

# 发布到 PyPI
uv publish

# 发布到 Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/

# 运行全部测试
pytest tests/

# 运行单个测试文件
pytest tests/test_client.py -v

# 运行测试服务器（单独验证）
python -m tests.test_server

# 启动 TUI 调试工具（--server 支持模块路径或文件路径）
rcptui --server tests.test_server
uv run rcptui --server path/to/server.py
```

## 核心架构

项目采用三层继承架构：

```
RPCServer
├── StdioStream    # 标准输入输出的读写能力
├── RPCRouter      # 路由注册和分发功能
└── AppDoc         # API 文档生成功能
```

### 文件结构

```
src/okstdio/
├── __init__.py                      # 导出 ClientManager, BroadcastResult
├── general/
│   ├── jsonrpc_model.py            # JSON-RPC 数据模型
│   └── errors.py                   # 错误处理（7个标准错误类）
├── server/
│   ├── application.py              # RPCServer, IOWrite
│   ├── router.py                   # RPCRouter, MethodsDict, MiddlewaresList
│   ├── middleware.py               # MiddlewareManager
│   ├── dependencies.py             # DependencyContainer
│   ├── stream.py                   # StdioStream, PackStreamReader/Writer
│   └── appdoc.py                   # AppDoc（文档生成、方法树）
├── client/
│   ├── application.py              # RPCClient, StreamListener
│   ├── future.py                   # RPCFuture（链式调用）
│   └── manager.py                  # ClientManager, BroadcastResult
└── tui/
    ├── __init__.py                  # 导出 OkstdioApp, run_app
    ├── app.py                       # OkstdioApp（主应用）
    ├── client.py                    # TUIClient（带钩子的客户端）
    ├── oktui.scss                   # 样式文件
    └── widgets/
        ├── method_tree.py           # MethodTreeWidget
        ├── params_editor.py         # ParamsEditor
        └── response_viewer.py       # ResponseViewer
```

### 关键组件

- **RPCServer** (`src/okstdio/server/application.py`): 核心服务器类，处理请求分发、依赖注入、中间件管理
- **IOWrite** (`src/okstdio/server/application.py`): 内置依赖，服务器主动推送消息到客户端
- **RPCClient** (`src/okstdio/client/application.py`): 客户端类，管理子进程生命周期和请求发送
- **RPCFuture** (`src/okstdio/client/future.py`): Promise 风格链式调用，支持 `.then()` 和 `.error()`
- **StreamListener** (`src/okstdio/client/application.py`): 流式监听器，支持 `async for` 迭代
- **ClientManager** (`src/okstdio/client/manager.py`): 批量管理多个 RPCClient，支持广播
- **DependencyContainer** (`src/okstdio/server/dependencies.py`): 轻量级依赖注入容器，支持单例/非单例
- **RPCRouter** (`src/okstdio/server/router.py`): 路由系统，支持方法注册、中间件和嵌套路由
- **MiddlewareManager** (`src/okstdio/server/middleware.py`): 链式执行中间件
- **StdioStream** (`src/okstdio/server/stream.py`): 跨平台异步 I/O（Windows 用 `asyncio.to_thread`，Unix 用 `add_reader`）
- **AppDoc** (`src/okstdio/server/appdoc.py`): 文档生成器，提供 `get_method_tree()` 供 TUI 和客户端使用
- **OkstdioApp** (`src/okstdio/tui/app.py`): TUI 调试工具主应用
- **TUIClient** (`src/okstdio/tui/client.py`): 继承 RPCClient，带 on_send/on_recv/on_push 钩子

### 消息流程

```
父进程 (RPCClient)                    子进程 (RPCServer)
       |                                    |
       |--- JSON-RPC Request (stdin) -----> |
       |                                    |--> 中间件链 --> 方法执行
       |<-- JSON-RPC Response (stdout) ---- |
       |                                    |
       |<----- IOWrite 推送 (stdout) -------|  (可选：流式响应)
```

## 客户端调用模式

### 传统模式（send + await）
```python
future = await client.send("method", {"param": "value"})
response = await future
print(response.result)
```

### 链式调用（call + then）
```python
await client.call("method", {"param": "value"}).then(
    lambda result: print(result)
).error(
    lambda err: print(err)
)
```

### 流式响应接收
```python
async with client.stream("push_id") as listener:
    future = await client.send("long_task", {})
    async for message in listener:
        print(message)
```

## 依赖注入系统

RPCServer 内置依赖注入容器，自动注入参数：

```python
app.register_dependency(Database, lambda: Database(), singleton=True)

@app.add_method()
def get_user(db: Database) -> dict:
    return db.query(...)

# IOWrite 自动注册，无需手动配置
@app.add_method()
async def long_task(io_write: IOWrite):
    await io_write.write({"progress": 50})
```

## 技术栈

- Python 3.10+
- Pydantic 2.x (参数验证和序列化)
- asyncio (异步 I/O)
- Textual（可选，TUI 支持）
- uv (包管理器，构建后端: uv_build)

## 日志注意事项

确保日志只写入文件，不输出到 stdout，避免干扰 JSON-RPC 通信：

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("app.log", maxBytes=2*1024*1024, encoding="utf-8")
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(handler)
```

## 路由命名约定

方法路径格式：`{server_name}.{router_prefix}.{method_name}`

系统方法使用 `__` 前缀（如 `__system__`），不经过中间件处理。

## TUI 调试工具

### TUI 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+j | 发送请求 |
| Ctrl+r | 重启服务器 |
| Ctrl+l | 清理日志 |
| Ctrl+q | 退出 |

### TUI 组件结构

- **OkstdioApp**: 基于 textual.App 的主应用，管理整体布局和状态
- **TUIClient**: 继承 RPCClient，通过 on_send/on_recv/on_push 钩子与 UI 通信
- **MethodTreeWidget**: 基于 textual.Tree 的方法树，递归展示服务器方法
- **ParamsEditor**: 基于 textual.TextArea 的参数编辑器，支持 JSON 语法高亮
- **ResponseViewer**: 基于 textual.TabbedContent 的响应查看器（Response + Log）

### 开发 TUI 组件

```python
from textual.app import App, ComposeResult
from textual.widgets import Tree

class MyTree(Tree):
    def compose(self) -> ComposeResult:
        yield SomeWidget()
```
