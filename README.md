# OkStdio

**基于 Stdio 的 JSON-RPC 父子进程通信框架**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

OkStdio 是一个轻量级的 Python 框架，通过标准输入输出（stdin/stdout）实现父子进程之间的 JSON-RPC 2.0 通信。提供优雅的 API 设计、强类型支持、链式调用、流式响应、中间件机制和自动文档生成。

## 特性

- ✅ **JSON-RPC 2.0 标准**：完整实现 JSON-RPC 2.0 协议规范
- ✅ **基于 Stdio**：通过标准输入输出通信，轻量且跨平台
- ✅ **强类型支持**：基于 Pydantic 的参数验证和序列化
- ✅ **异步优先**：完整的 asyncio 支持
- ✅ **链式调用**：`call().then().error()` 的 Promise 风格链式 API
- ✅ **流式响应**：`async for` 流式接收服务器推送（StreamListener）
- ✅ **中间件机制**：灵活的请求/响应拦截处理
- ✅ **路由系统**：支持方法前缀和嵌套路由
- ✅ **依赖注入**：支持单例/非单例、运行时动态注册
- ✅ **批量管理**：ClientManager 管理多客户端，支持广播请求
- ✅ **自动文档**：自动生成 Markdown 格式的 API 文档
- ✅ **服务器方法树**：通过 `__system__` 系统方法获取完整方法树
- ✅ **TUI 调试工具**：内置文本用户界面调试工具 `rcptui`
- ✅ **跨平台**：Windows/Linux/macOS 全平台支持，自动处理编码

## 安装

```bash
pip install okstdio

# 包含 TUI 调试工具
pip install "okstdio[tui]"
```

或使用 uv（推荐）：

```bash
uv add okstdio
uv add "okstdio[tui]"
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

        # 方式一：send() + await（传统风格）
        future = await client.send("get_user", {"user_id": 1})
        response = await future
        print(response.result)

        # 方式二：call().then()（链式风格）
        await client.call("get_user", {"user_id": 1}).then(
            lambda result: print(result)
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## 核心概念

### 1. 服务器 (RPCServer)

```python
from okstdio.server import RPCServer, RPCRouter

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

```python
from okstdio.client import RPCClient

async with RPCClient("client_name") as client:
    await client.start("example.server")    # 模块方式
    # await client.start("path/to/server.py")  # 脚本方式

    # 传统方式
    future = await client.send("user.create", {"username": "alice"})
    response = await future

    # 链式调用
    await client.call("user.create", {"username": "alice"}).then(
        lambda result: print(result)
    )
```

### 3. 链式调用 (RPCFuture)

`call()` 返回 `RPCFuture`，支持 `.then()` 和 `.error()` 链式处理：

```python
from pydantic import BaseModel

class UserResult(BaseModel):
    id: int
    username: str

# 自动注入 Pydantic 模型
await client.call("user.create", {"username": "alice"}).then(
    lambda user: print(f"创建成功: {user.username}"),  # user 是 UserResult 实例
    extra_params={"user": UserResult}  # 类型提示
)

# 使用参数名约定
await client.call("user.create", {"username": "alice"}).then(
    lambda result: print(result)    # result → response.result
).error(
    lambda err: print(f"出错: {err}")
)

# 后台任务（不阻塞）
client.call("long_task", {}).then(on_done, create_task=True)
```

`.then()` 参数注入规则：
1. 参数类型为 `BaseModel` 子类 → 用 `response.result` 实例化该模型
2. `extra_params` 中有同名 key → 注入对应值
3. 参数名为 `result` → 注入 `response.result`
4. 参数名为 `response` → 注入完整 `JSONRPCResponse`
5. 其余 → 注入 `response.result`

### 4. 流式响应 (IOWrite + StreamListener)

**服务器端** 通过 `IOWrite` 推送：

```python
from okstdio.server import IOWrite

@app.add_method(name="long_task")
async def long_task(io_write: IOWrite) -> dict:
    for i in range(10):
        await io_write.write({"progress": i * 10, "status": "running"})
        await asyncio.sleep(1)
    return {"status": "completed"}
```

**客户端** 通过 `stream()` 上下文管理器接收：

```python
# 推荐：async for 迭代（自动结束）
async with client.stream("progress") as listener:
    future = await client.send("long_task", {})
    async for message in listener:
        print(f"进度: {message}")

# 手动：监听队列
queue = client.add_listen_queue("progress")
future = await client.send("long_task", {})
while True:
    msg = await queue.get()
    if msg is None:
        break
    print(msg)
```

### 5. 中间件

```python
@app.add_middleware(label="日志中间件")
async def log_middleware(request, call_next):
    print(f"收到请求: {request.method}")
    response = await call_next(request)
    print(f"返回响应: {response}")
    return response
```

### 6. 依赖注入

```python
import uiautomator2 as u2

# 注册单例依赖
app.register_dependency(
    u2.Device,
    lambda: u2.connect("192.168.1.100:5555"),
    singleton=True
)

@app.add_method()
def click_device(device: u2.Device) -> dict:
    device.click(0.5, 0.5)
    return {"status": "clicked"}

# 运行时动态注册
@app.add_method()
def init_device(device_ip: str) -> dict:
    device = u2.connect(device_ip)
    app.register_dependency(u2.Device, lambda: device, singleton=True)
    return {"status": "device registered"}

# 检查依赖
if app.has_dependency(u2.Device):
    device = app.get_dependency(u2.Device)
```

### 7. 批量客户端管理 (ClientManager)

```python
from okstdio import ClientManager

async with ClientManager() as manager:
    # 添加多个客户端
    await manager.add("server1", "module.server1")
    await manager.add("server2", "module.server2")

    # 并发启动所有
    await manager.start_all()

    # 单独调用
    result = await manager.send_to("server1", "method", {"param": "value"})
    await manager.call_to("server2", "method", {"param": "value"}).then(
        lambda result: print(result)
    )

    # 广播请求（不抛异常，独立封装结果）
    results = await manager.broadcast("health_check", {})
    for r in results:
        if r.error:
            print(f"{r.client_name} 失败: {r.error}")
        else:
            print(f"{r.client_name} 结果: {r.result}")
```

### 8. 服务器方法树

```python
# 客户端获取服务器方法树
method_tree = await client.get_server_methods()
print("服务器名称:", method_tree["server_name"])
print("服务器版本:", method_tree["version"])

for method in method_tree["methods"]:
    print(f"- {method['name']} ({method['path']}): {method['doc']}")
```

方法树结构：
- `server_name`: 服务器名称
- `version`: 服务器版本
- `label`: 服务器标签
- `methods`: 方法列表（name, label, path, doc, params, results）
- `middlewares`: 中间件列表
- `routers`: 路由器字典

### 9. TUI 调试工具

```bash
# 使用模块路径启动
rcptui --server tests.test_server

# 使用脚本路径
rcptui --server path/to/server.py

# 使用 uv
uv run rcptui --server tests.test_server
```

界面布局：

```
┌──────────────────────────────────────────────────────────────────┐
│ Header                                                           │
├───────────────────┬──────────────────────────────────────────────┤
│ Method Tree       │ Method: 方法名 [标签]                        │
│ ▼ Server          ├──────────────────────────────────────────────┤
│ ├── 方法1         │ Params (JSON):                               │
│ ├── 方法2         │ {                                            │
│ └──▶ 子路由       │   "user_id": 123                             │
│    ├── 方法1      │ }                                            │
│    └── 方法2      ├──────────────────────────────────────────────┤
│                   │ Response | Log                               │
│                   ├──────────────────────────────────────────────┤
│                   │ # 格式化的 JSON 响应                          │
│                   │ # 或请求/响应日志                             │
├───────────────────┴──────────────────────────────────────────────┤
│ Footer: Ctrl+j 发送 | Ctrl+r 重启 | Ctrl+l 清日志 | Ctrl+q 退出  │
└──────────────────────────────────────────────────────────────────┘
```

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+j` | 发送请求 |
| `Ctrl+r` | 重启服务器 |
| `Ctrl+l` | 清理日志 |
| `Ctrl+q` | 退出 |

## 自动文档生成

```python
if __name__ == "__main__":
    app.docs_markdown()  # 生成 {server_name}.md
    app.runserver()
```

## 错误处理

```python
from okstdio.general.errors import (
    RPCParseError,           # -32700: 语法解析错误
    RPCInvalidRequestError,  # -32600: 无效请求
    RPCMethodNotFoundError,  # -32601: 找不到方法
    RPCInvalidParamsError,   # -32602: 无效参数
    RPCInternalError,        # -32603: 内部错误
    RPCServerError,          # -32000~-32099: 服务器错误
)

# 自定义错误响应
from okstdio.general.jsonrpc_model import JSONRPCServerErrorDetail

@app.add_method(name="restricted")
def restricted_method() -> dict | JSONRPCServerErrorDetail:
    return JSONRPCServerErrorDetail(code=-32001, message="权限不足")
```

## 最佳实践

### 日志配置

确保日志只写入文件，不输出到 stdout（避免干扰 JSON-RPC 通信）：

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("app.log", maxBytes=2*1024*1024, encoding="utf-8")
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(handler)
```

### 编码问题

在 Windows 上，框架会自动将 stdin/stdout 重新包装为 UTF-8，无需手动配置。

### Pydantic 模型设计

```python
class CreateUserParams(BaseModel):
    username: str = Field(..., min_length=3)
    email: str = Field(..., description="邮箱")
    age: int = Field(..., ge=0, le=120)

@app.add_method(name="create_user")
def create_user(params: CreateUserParams) -> dict:
    return {"id": 1, **params.model_dump()}
```

## 技术栈

- **Python 3.10+**：利用现代 Python 特性
- **Pydantic 2.x**：数据验证和序列化
- **asyncio**：异步 I/O 支持
- **Textual**（可选）：TUI 界面框架

## 完整示例

查看 `example/` 目录了解完整示例，包括英雄管理系统服务器/客户端实现。

```bash
python -m example.client
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Textual 文档](https://textual.textualize.io/)
- [示例项目](example/)

---

**作者**: jianjian
**邮箱**: jianjian2048@gmail.com
