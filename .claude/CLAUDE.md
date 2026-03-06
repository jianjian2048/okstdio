# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

okstdio-enhance 是一个基于 Stdio 的 JSON-RPC 父子进程通信框架，实现了 JSON-RPC 2.0 协议规范。

## 常用命令

```bash
# 安装依赖
uv sync

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

### 关键组件

- **RPCServer** (`src/okstdio/server/application.py`): 核心服务器类，处理请求分发、依赖注入、中间件管理
- **RPCClient** (`src/okstdio/client/application.py`): 客户端类，管理子进程生命周期和请求发送
- **DependencyContainer** (`src/okstdio/server/dependencies.py`): 轻量级依赖注入容器，支持单例/非单例模式
- **RPCRouter** (`src/okstdio/server/router.py`): 路由系统，支持方法注册、中间件和嵌套路由
- **MiddlewareManager** (`src/okstdio/server/middleware.py`): 链式执行中间件，支持请求前/后处理
- **StdioStream** (`src/okstdio/server/stream.py`): 跨平台异步 I/O（Windows 用 `asyncio.to_thread`，Unix 用事件循环 `add_reader`）
- **AppDoc** (`src/okstdio/server/appdoc.py`): 文档生成器，提供 `get_method_tree()` 供 TUI 和客户端使用
- **JSONRPCRequest/Response/Error** (`src/okstdio/general/jsonrpc_model.py`): 核心数据模型
- **RPCError 错误体系** (`src/okstdio/general/errors.py`): JSON-RPC 2.0 标准错误码（-32700 ~ -32000）
- **IOWrite**: 内置依赖，用于服务器主动推送消息到客户端
- **OkstdioApp** (`src/okstdio/tui/app.py`): TUI 调试工具主应用
- **MethodTreeWidget** (`src/okstdio/tui/widgets/method_tree.py`): 方法树显示组件
- **ParamsEditor** (`src/okstdio/tui/widgets/params_editor.py`): 参数编辑器组件
- **ResponseViewer** (`src/okstdio/tui/widgets/response_viewer.py`): 响应和日志查看器

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

## 客户端流式响应

服务器通过 `IOWrite` 主动推送时，客户端需要注册监听队列接收推送：

```python
async with RPCClient("test_server") as client:
    await client.start("tests.test_server")
    queue = client.add_listen_queue("progress")  # 监听 id="progress" 的推送
    future = await client.send("test_server.long_task", {})
    while True:
        push_msg = await queue.get()  # 接收推送消息
        if push_msg is None:
            break
    result = await future
```

## 依赖注入系统

RPCServer 内置依赖注入容器，自动注入参数：

```python
# 注册依赖
app.register_dependency(Database, lambda: Database(), singleton=True)

# 方法中自动注入
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

### 组件结构

```
src/okstdio/tui/
├── __init__.py              # 导出 OkstdioApp 和 run_app 入口
├── app.py                   # 主应用类 OkstdioApp
├── oktui.scss               # TUI 样式文件
└── widgets/
    ├── __init__.py          # widgets 模块入口
    ├── method_tree.py       # MethodTreeWidget 方法树组件
    ├── params_editor.py     # ParamsEditor 参数编辑器
    └── response_viewer.py   # ResponseViewer 响应查看器
```

### TUI 组件说明

- **OkstdioApp**: 基于 textual.App 的主应用，管理整体布局和状态
- **MethodTreeWidget**: 基于 textual.Tree 的方法树，递归展示服务器方法
- **ParamsEditor**: 基于 textual.TextArea 的参数编辑器，支持 JSON 语法高亮
- **ResponseViewer**: 基于 textual.TabbedContent 的响应查看器，包含 Response 和 Log 两个标签页

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+j | 发送请求 |
| Ctrl+r | 重启服务器 |
| Ctrl+q | 退出 |

### 开发 TUI 组件

TUI 模块使用 Textual 框架，遵循 Textual 的组件开发模式：

```python
from textual.app import App, ComposeResult
from textual.widgets import Tree

class MyTree(Tree):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield SomeWidget()
```
