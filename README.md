# OkStdio

**基于 Stdio 的 JSON-RPC 父子进程通信框架**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

OkStdio 是一个轻量级的 Python 框架，通过标准输入输出（stdin/stdout）实现父子进程之间的 JSON-RPC 2.0 通信。它提供了优雅的 API 设计、强类型支持、中间件机制以及自动文档生成功能。

## 特性

- ✅ **JSON-RPC 2.0 标准**：完整实现 JSON-RPC 2.0 协议规范
- ✅ **基于 Stdio**：通过标准输入输出进行通信，轻量且跨平台
- ✅ **强类型支持**：基于 Pydantic 的参数验证和序列化
- ✅ **异步优先**：完整的 asyncio 支持，适合 I/O 密集型任务
- ✅ **中间件机制**：灵活的请求/响应拦截和处理
- ✅ **路由系统**：支持方法前缀和嵌套路由
- ✅ **自动文档**：自动生成 Markdown 格式的 API 文档
- ✅ **流式响应**：支持服务器主动推送消息（IOWrite）
- ✅ **跨平台**：Windows/Linux/macOS 全平台支持，自动处理编码问题

## 安装

```bash
pip install okstdio
```

或使用 uv（推荐）：

```bash
uv add okstdio
```

## 快速开始

### 服务器端

```python
from okstdio.server import RPCServer
from pydantic import BaseModel, Field

app = RPCServer("my_server", label="我的服务器")

class User(BaseModel):
    name: str = Field(..., description="用户名")
    age: int = Field(..., ge=0, le=120, description="年龄")

@app.add_method(name="get_user", label="获取用户")
def get_user(user_id: int) -> User:
    """根据 ID 获取用户信息"""
    return User(name="张三", age=25)

if __name__ == "__main__":
    app.runserver()
```

### 客户端

```python
import asyncio
from okstdio.client import RPCClient

async def main():
    async with RPCClient("my_client") as client:
        await client.start("my_server")  # 启动服务器进程
        
        future = await client.send("get_user", {"user_id": 1})
        response = await future
        print(response.result)  # {"name": "张三", "age": 25}

if __name__ == "__main__":
    asyncio.run(main())
```

## 核心概念

### 1. 服务器 (RPCServer)

服务器负责接收和处理 JSON-RPC 请求：

```python
from okstdio.server import RPCServer, RPCRouter

# 创建服务器实例
app = RPCServer("example_server", label="示例服务器", version="v1.0.0")

# 注册方法
@app.add_method(name="hello", label="问候")
def hello(name: str) -> str:
    return f"Hello, {name}!"

# 路由分组
user_router = RPCRouter(prefix="user", label="用户管理")

@user_router.add_method(name="create")
def create_user(username: str) -> dict:
    return {"id": 1, "username": username}

app.include_router(user_router)
```

### 2. 客户端 (RPCClient)

客户端用于与服务器进程通信：

```python
from okstdio.client import RPCClient

async with RPCClient("client_name") as client:
    # 启动服务器（模块方式）
    await client.start("example.server")
    
    # 或启动脚本
    await client.start("path/to/server.py")
    
    # 发送请求
    future = await client.send("user.create", {"username": "alice"})
    response = await future
    
    # 监听流式响应
    queue = client.add_listen_queue(task_id)
    while True:
        message = await queue.get()
        print(message)
```

### 3. 中间件

中间件可以拦截和处理请求/响应：

```python
@app.add_middleware(label="日志中间件")
async def log_middleware(request, call_next):
    print(f"收到请求: {request.method}")
    response = await call_next(request)
    print(f"返回响应: {response}")
    return response
```

### 4. 流式响应 (IOWrite)

服务器可以主动推送消息给客户端：

```python
from okstdio.server import IOWrite

@app.add_method(name="stream_data")
async def stream_data(io_write: IOWrite) -> dict:
    for i in range(10):
        await io_write.write(JSONRPCResponse(
            id="stream-id",
            result={"progress": i * 10}
        ))
        await asyncio.sleep(1)
    return {"status": "completed"}
```

### 5. 类型注解

支持使用 `Annotated` 为参数添加验证和文档：

```python
from typing import Annotated
from pydantic import Field

@app.add_method(name="create_user")
def create_user(
    username: Annotated[str, Field(..., min_length=3, description="用户名")],
    age: Annotated[int, Field(..., ge=0, le=120, description="年龄")]
) -> dict:
    return {"username": username, "age": age}
```

## 自动文档生成

OkStdio 可以自动生成 Markdown 格式的 API 文档：

```python
if __name__ == "__main__":
    app.docs_markdown()  # 生成 {server_name}.md
    app.runserver()
```

生成的文档包含：
- 所有方法的签名、参数、返回值
- Pydantic 模型的字段说明
- 中间件列表
- 使用示例

## 完整示例

查看 `example/` 目录了解完整的示例项目，包括：
- **服务器** (`example/server.py`)：英雄管理系统，支持创建英雄、进入副本战斗
- **客户端** (`example/client.py`)：与服务器交互的示例客户端
- **数据模型** (`example/schemas.py`)：Pydantic 模型定义
- **数据库** (`example/databases.py`)：SQLite 数据库操作

运行示例：

```bash
# 启动客户端（会自动启动服务器）
python -m example.client
```

## 错误处理

OkStdio 提供了标准的 JSON-RPC 错误类型：

```python
from okstdio.general.errors import (
    RPCParseError,           # -32700: 语法解析错误
    RPCInvalidRequestError,  # -32600: 无效请求
    RPCMethodNotFoundError,  # -32601: 找不到方法
    RPCInvalidParamsError,   # -32602: 无效参数
    RPCInternalError,        # -32603: 内部错误
    RPCServerError,          # -32000~-32099: 服务器错误
)

# 自定义错误
from okstdio.general.jsonrpc_model import JSONRPCServerErrorDetail

@app.add_method(name="restricted")
def restricted_method() -> dict | JSONRPCServerErrorDetail:
    return JSONRPCServerErrorDetail(
        code=-32001,
        message="权限不足"
    )
```

## 最佳实践

### 1. 日志配置

确保日志只写入文件，不输出到 stdout（避免干扰 JSON-RPC 通信）：

```python
import logging
from logging.handlers import RotatingFileHandler

LOG_HANDLER = RotatingFileHandler(
    filename="app.log",
    maxBytes=2 * 1024 * 1024,
    encoding="utf-8"
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(LOG_HANDLER)
```

### 2. 编码问题

在 Windows 上，框架会自动将 stdin/stdout 重新包装为 UTF-8，无需手动配置。

### 3. 模型设计

使用 Pydantic 模型管理复杂参数：

```python
class CreateUserParams(BaseModel):
    username: str = Field(..., min_length=3)
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=120)

@app.add_method(name="create_user")
def create_user(params: CreateUserParams) -> dict:
    return {"id": 1, **params.model_dump()}
```

### 4. 异步任务

对于长时间运行的任务，使用 `IOWrite` 推送进度：

```python
@app.add_method(name="long_task")
async def long_task(io_write: IOWrite) -> dict:
    for i in range(100):
        await asyncio.sleep(0.1)
        await io_write.write(JSONRPCResponse(
            id="progress",
            result={"progress": i + 1}
        ))
    return {"status": "completed"}
```

## 技术栈

- **Python 3.10+**：利用现代 Python 特性
- **Pydantic 2.x**：数据验证和序列化
- **asyncio**：异步 I/O 支持
- **Jinja2**：文档模板引擎（可选）

## 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/okstdio.git
cd okstdio

# 安装开发依赖
uv sync --dev

# 运行测试
pytest tests/

# 运行示例
python -m example.client
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [示例项目](example/)

---

**作者**: jianjian  
**邮箱**: jianjian2048@gmail.com

