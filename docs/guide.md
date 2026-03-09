# OkStdio 开发指南

> 基于 Stdio 的 JSON-RPC 父子进程通信框架完整开发文档

## 目录

1. [快速入门](#1-快速入门)
2. [服务器开发](#2-服务器开发)
3. [客户端开发](#3-客户端开发)
4. [链式调用（RPCFuture）](#4-链式调用-rpcfuture)
5. [流式响应](#5-流式响应)
6. [中间件](#6-中间件)
7. [路由系统](#7-路由系统)
8. [依赖注入](#8-依赖注入)
9. [批量客户端管理（ClientManager）](#9-批量客户端管理-clientmanager)
10. [错误处理](#10-错误处理)
11. [TUI 调试工具](#11-tui-调试工具)
12. [自动文档生成](#12-自动文档生成)
13. [最佳实践](#13-最佳实践)
14. [API 参考](#14-api-参考)

---

## 1. 快速入门

### 安装

```bash
# 基础安装
pip install okstdio

# 含 TUI 调试工具
pip install "okstdio[tui]"

# 使用 uv（推荐）
uv add okstdio
uv add "okstdio[tui]"
```

### 5 分钟示例

**server.py**

```python
from okstdio.server import RPCServer

app = RPCServer("demo")

@app.add_method()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    app.runserver()
```

**client.py**

```python
import asyncio
from okstdio.client import RPCClient

async def main():
    async with RPCClient("demo_client") as client:
        await client.start("server")  # 启动 server.py 进程
        result = await client.call("demo.add", {"a": 1, "b": 2})
        print(await result)  # JSONRPCResponse(result=3)

asyncio.run(main())
```

> **注意**：方法路径格式为 `{server_name}.{method_name}`，上例中服务器名为 `demo`，方法名为 `add`，路径为 `demo.add`。

---

## 2. 服务器开发

### 2.1 创建服务器

```python
from okstdio.server import RPCServer

app = RPCServer(
    server_name="my_server",  # 服务器名称，影响方法路径前缀，默认 "app"
    label="我的服务器",        # 人类可读标签（可选）
    version="v1.0.0"          # 版本号（可选）
)

if __name__ == "__main__":
    app.runserver()
```

### 2.2 注册方法

```python
# 基础方法
@app.add_method(name="hello", label="问候")
def hello(name: str) -> str:
    """向用户发出问候"""
    return f"Hello, {name}!"

# name 默认使用函数名
@app.add_method()
def ping() -> str:
    return "pong"

# 异步方法
@app.add_method()
async def fetch_data(url: str) -> dict:
    # 支持异步操作
    return {"url": url, "data": "..."}
```

### 2.3 参数类型支持

框架自动根据函数签名进行参数验证：

```python
from typing import Annotated
from pydantic import BaseModel, Field

# 基础类型
@app.add_method()
def basic_types(
    name: str,
    age: int,
    active: bool,
    score: float
) -> dict:
    return {"name": name, "age": age}

# Pydantic 模型
class CreateUserParams(BaseModel):
    username: str = Field(..., min_length=3, description="用户名")
    email: str = Field(..., description="邮箱")
    age: int = Field(default=18, ge=0, le=120)

@app.add_method()
def create_user(params: CreateUserParams) -> dict:
    return {"id": 1, **params.model_dump()}

# Annotated 类型注解（更细粒度的验证）
@app.add_method()
def annotated_params(
    username: Annotated[str, Field(min_length=3, description="用户名")],
    age: Annotated[int, Field(ge=0, le=120, description="年龄")]
) -> dict:
    return {"username": username, "age": age}
```

### 2.4 返回值

```python
from okstdio.general.jsonrpc_model import JSONRPCServerErrorDetail

# 返回字典
@app.add_method()
def get_info() -> dict:
    return {"version": "1.0.0"}

# 返回 Pydantic 模型（自动序列化）
class UserInfo(BaseModel):
    id: int
    name: str

@app.add_method()
def get_user(user_id: int) -> UserInfo:
    return UserInfo(id=user_id, name="张三")

# 返回自定义错误
@app.add_method()
def restricted() -> dict | JSONRPCServerErrorDetail:
    if not has_permission():
        return JSONRPCServerErrorDetail(code=-32001, message="权限不足")
    return {"data": "..."}
```

---

## 3. 客户端开发

### 3.1 创建客户端

```python
from okstdio.client import RPCClient

# 上下文管理器（推荐）
async with RPCClient("client_name") as client:
    await client.start("server_module")
    # ... 使用客户端

# 手动管理
client = RPCClient("client_name")
await client.start("server_module")
try:
    # ... 使用客户端
finally:
    await client.stop()
```

### 3.2 启动服务器进程

```python
# 模块路径（推荐）
await client.start("mypackage.server")

# Python 脚本
await client.start("path/to/server.py")

# 带额外参数
await client.start("mypackage.server", "--port", "8080")
```

**自动判断逻辑**：
- 包含 `/` 或 `\` 或以 `.py` 结尾 → 视为脚本路径，用 `python path/to/server.py` 启动
- 否则 → 视为模块路径，用 `python -m module.path` 启动

### 3.3 发送请求

```python
# send()：返回 asyncio.Future，需要两次 await
future = await client.send("server.method", {"param": "value"})
response = await future
print(response.result)

# call()：返回 RPCFuture，支持链式调用（详见第4节）
await client.call("server.method", {"param": "value"}).then(
    lambda result: print(result)
)

# 自定义 request_id
future = await client.send("server.method", {}, request_id="my-id-001")
```

---

## 4. 链式调用（RPCFuture）

`client.call()` 返回 `RPCFuture`，提供 Promise 风格的链式 API。

### 4.1 基础用法

```python
# 直接 await（等同于 send + await）
response = await client.call("method", {"param": "value"})
print(response.result)

# .then() 处理成功结果
await client.call("method", {"param": "value"}).then(
    lambda result: print(result)
)

# .error() 处理错误
await client.call("method", {"param": "value"}).then(
    lambda result: print(result)
).error(
    lambda err: print(f"错误: {err}")
)
```

### 4.2 .then() 参数注入规则

`.then()` 会根据回调函数的参数签名自动注入合适的值：

```python
# 规则1：参数类型为 BaseModel 子类 → 用 response.result 实例化该模型
class UserResult(BaseModel):
    id: int
    username: str

await client.call("create_user", {"username": "alice"}).then(
    lambda user: print(user.username),  # user 自动是 UserResult 实例
    extra_params={"user": UserResult}    # 声明类型
)

# 规则2：参数名为 "result" → 注入 response.result（原始值）
await client.call("method", {}).then(
    lambda result: print(result)
)

# 规则3：参数名为 "response" → 注入完整 JSONRPCResponse
await client.call("method", {}).then(
    lambda response: print(response.id, response.result)
)

# 规则4：async 回调
async def async_handler(result):
    await asyncio.sleep(0.1)
    print(result)

await client.call("method", {}).then(async_handler)
```

### 4.3 后台任务模式

```python
# create_task=True：不等待，创建后台任务
client.call("long_task", {}).then(
    lambda result: print(f"完成: {result}"),
    create_task=True
)
# 不需要 await，立即返回
```

---

## 5. 流式响应

用于服务器长时间运行任务向客户端推送进度。

### 5.1 服务器端：IOWrite

`IOWrite` 是内置依赖，在方法参数中声明即可自动注入：

```python
from okstdio.server import IOWrite

@app.add_method(name="long_task")
async def long_task(io_write: IOWrite) -> dict:
    for i in range(10):
        # 推送进度（id 用于客户端匹配监听）
        await io_write.write({"progress": i * 10, "status": "running"})
        await asyncio.sleep(1)
    # 方法返回值作为最终 JSON-RPC 响应
    return {"status": "completed", "total": 10}
```

`io_write.write()` 接受：
- `dict`：自动包装成 JSON-RPC 响应
- `JSONRPCResponse`：直接写入

### 5.2 客户端端：stream() 上下文管理器（推荐）

```python
# stream(listen_id) 自动注册和清理监听队列
async with client.stream("progress") as listener:
    future = await client.send("server.long_task", {})
    async for message in listener:
        print(f"收到推送: {message}")
    # listener 结束后，等待最终响应
    response = await future
    print(f"最终结果: {response.result}")
```

### 5.3 客户端端：手动监听队列

```python
# 手动方式（需要自己管理生命周期）
queue = client.add_listen_queue("progress")
try:
    future = await client.send("server.long_task", {})
    while True:
        msg = await queue.get()
        if msg is None:  # None 表示流结束
            break
        print(f"收到: {msg}")
    response = await future
finally:
    client.del_listen_queue("progress")
```

### 5.4 StreamListener 的 async for 迭代

```python
from okstdio.client import RPCClient

# StreamListener 支持超时设置
async with client.stream("task_id", timeout=30.0) as listener:
    future = await client.send("server.long_task", {})
    async for msg in listener:
        print(msg)
        # 超时后自动停止迭代
```

---

## 6. 中间件

中间件采用洋葱模型，支持请求前/后的处理逻辑。

### 6.1 注册中间件

```python
@app.add_middleware(label="日志中间件")
async def log_middleware(request, call_next):
    # 请求前处理
    print(f"[{request.id}] 收到请求: {request.method}")

    # 调用下一个中间件或实际处理函数
    response = await call_next(request)

    # 请求后处理
    print(f"[{request.id}] 返回响应")
    return response
```

### 6.2 中间件执行顺序

多个中间件按注册顺序形成链式调用：

```python
@app.add_middleware(label="中间件1")
async def middleware1(request, call_next):
    print("MW1 before")
    response = await call_next(request)
    print("MW1 after")
    return response

@app.add_middleware(label="中间件2")
async def middleware2(request, call_next):
    print("MW2 before")
    response = await call_next(request)
    print("MW2 after")
    return response

# 执行顺序：MW1 before → MW2 before → 方法执行 → MW2 after → MW1 after
```

### 6.3 中间件拦截请求

```python
from okstdio.general.errors import RPCServerError
from okstdio.general.jsonrpc_model import JSONRPCError, JSONRPCErrorDetail

@app.add_middleware(label="鉴权中间件")
async def auth_middleware(request, call_next):
    # 拦截并返回错误（不调用 call_next）
    if not is_authenticated(request):
        return JSONRPCError(
            id=request.id,
            error=JSONRPCErrorDetail(code=-32001, message="未授权")
        )
    return await call_next(request)
```

> **注意**：系统方法（`__system__` 等 `__` 前缀方法）不经过中间件。

---

## 7. 路由系统

使用路由器对方法进行分组管理。

### 7.1 创建路由器

```python
from okstdio.server import RPCRouter

user_router = RPCRouter(prefix="user", label="用户管理")

@user_router.add_method(name="create", label="创建用户")
def create_user(username: str) -> dict:
    return {"id": 1, "username": username}

@user_router.add_method(name="delete")
def delete_user(user_id: int) -> dict:
    return {"deleted": user_id}

# 挂载路由器
app.include_router(user_router)
```

方法路径：`{server_name}.{prefix}.{method_name}`
例：`my_server.user.create`

### 7.2 嵌套路由

```python
admin_router = RPCRouter(prefix="admin", label="管理员")
user_router = RPCRouter(prefix="user", label="用户")

@user_router.add_method(name="list")
def list_users() -> list:
    return []

admin_router.include_router(user_router)  # 嵌套
app.include_router(admin_router)

# 方法路径：my_server.admin.user.list
```

### 7.3 路由器中间件

中间件可以注册在路由器上，只对该路由器的方法生效：

```python
@user_router.add_middleware(label="用户权限检查")
async def user_auth(request, call_next):
    # 只对 user 路由下的方法生效
    return await call_next(request)
```

---

## 8. 依赖注入

`DependencyContainer` 提供轻量级依赖注入。

### 8.1 注册依赖

```python
import uiautomator2 as u2

# 单例模式（全局唯一，适合设备连接、数据库连接）
app.register_dependency(
    u2.Device,
    lambda: u2.connect("192.168.1.100:5555"),
    singleton=True
)

# 非单例模式（每次请求新实例，适合请求上下文）
app.register_dependency(
    Session,
    lambda: Session(),
    singleton=False
)

# 字符串 key
app.register_dependency(
    "db_factory",
    lambda: lambda url: Database(url),
    singleton=True
)
```

### 8.2 方法中自动注入

参数类型匹配依赖容器中已注册的类型时，自动注入：

```python
@app.add_method()
def click_device(device: u2.Device) -> dict:
    device.click(0.5, 0.5)
    return {"status": "clicked"}

# 支持子类匹配
class MyDevice(u2.Device): ...

app.register_dependency(MyDevice, lambda: MyDevice(), singleton=True)

@app.add_method()
def use_device(device: u2.Device) -> dict:  # 注入 MyDevice 实例
    return {"ok": True}
```

### 8.3 运行时动态注册

```python
@app.add_method()
def init_device(device_ip: str, device_port: int) -> dict:
    device = u2.connect(f"{device_ip}:{device_port}")
    # 运行时注册
    app.register_dependency(u2.Device, lambda: device, singleton=True)
    return {"status": "device registered"}
```

### 8.4 IOWrite 内置依赖

`IOWrite` 是框架内置的特殊依赖，无需手动注册：

```python
from okstdio.server import IOWrite

@app.add_method()
async def long_task(io_write: IOWrite) -> dict:
    await io_write.write({"progress": 50})
    return {"done": True}
```

### 8.5 使用 Inject 标记显式声明依赖

隐式依赖注入（按类型自动匹配容器）会导致这些参数出现在自动生成的 API 文档和 TUI 调试器中，令人混淆。使用 `Annotated[T, Inject()]` 可显式标记参数为依赖注入，使其从文档中排除。

```python
from typing import Annotated
from okstdio import Inject  # 或 from okstdio.server import Inject

@app.add_method("debug")
def debug(
    device: Annotated[u2.Device, Inject()],  # 依赖，不出现在文档
    keyword: str                              # 普通参数，出现在文档
) -> dict:
    device(text=keyword).click()
    return {"status": "ok"}
```

`Inject` 标记的参数：
- **被 TUI 调试器和 API 文档忽略**，不生成参数模板
- **仍由依赖容器自动注入**，运行时行为不变
- 适用于静态注册和运行时动态注册的依赖

与运行时注册搭配使用：

```python
@app.add_method("init_device")
def init_device(serial: str) -> dict:
    device = u2.connect(serial)
    app.register_dependency(u2.Device, lambda: device, singleton=True)
    return {"status": "ok"}

@app.add_method("click")
def click(device: Annotated[u2.Device, Inject()], text: str) -> dict:
    device(text=text).click()
    return {"status": "ok"}
```

> **注意**：`IOWrite` 不需要 `Inject` 标记，框架已内置处理。

### 8.6 依赖检查

```python
# 检查是否注册
if app.has_dependency(u2.Device):
    device = app.get_dependency(u2.Device)

# 字符串 key 检查
if app.has_dependency("db_factory"):
    factory = app.get_dependency("db_factory")
```

---

## 9. 批量客户端管理（ClientManager）

`ClientManager` 用于管理多个 RPCClient，适合需要同时与多个服务器交互的场景。

### 9.1 基础用法

```python
from okstdio import ClientManager

async with ClientManager() as manager:
    # 添加客户端
    await manager.add("server1", "module.server1")
    await manager.add("server2", "module.server2", "--extra-arg")

    # 并发启动所有
    await manager.start_all()

    # 访问单个客户端
    client = manager.get("server1")
    # 或
    client = manager["server1"]

    # 检查是否存在
    if "server1" in manager:
        print(f"共 {len(manager)} 个客户端")
```

### 9.2 发送请求

```python
# 向指定客户端发送（传统 future 风格）
future = await manager.send_to("server1", "method", {"param": "value"})
response = await future

# 链式调用风格
await manager.call_to("server1", "method", {"param": "value"}).then(
    lambda result: print(result)
)
```

### 9.3 广播请求

向所有（或指定）客户端发送同一请求，不抛异常，独立封装每个结果：

```python
from okstdio import BroadcastResult

# 广播给所有客户端
results: list[BroadcastResult] = await manager.broadcast(
    "health_check", {}
)

for r in results:
    if r.error:
        print(f"{r.client_name} 失败: {r.error}")
    else:
        print(f"{r.client_name} 结果: {r.result}")

# 广播给指定客户端
results = await manager.broadcast(
    "method", {"param": "value"},
    targets=["server1", "server2"],
    timeout=10.0
)
```

`BroadcastResult` 字段：
- `client_name`: 客户端名称
- `result`: 成功时的结果（等于 `response.result`）
- `response`: 完整 `JSONRPCResponse`（成功时）
- `error`: 异常对象（失败时）

### 9.4 管理客户端

```python
# 添加已有客户端实例
existing_client = RPCClient("existing")
await existing_client.start("module.server")
manager.add_client(existing_client)

# 移除客户端（不停止进程）
manager.remove("server1")

# 移除并停止客户端
await manager.remove_and_stop("server1")

# 停止所有
await manager.stop_all()

# 获取所有客户端名称
names = manager.client_names
```

---

## 10. 错误处理

### 10.1 标准 JSON-RPC 错误

```python
from okstdio.general.errors import (
    RPCError,                # 基类
    RPCParseError,           # -32700: JSON 语法解析错误
    RPCInvalidRequestError,  # -32600: 无效 JSON-RPC 请求
    RPCMethodNotFoundError,  # -32601: 方法未找到
    RPCInvalidParamsError,   # -32602: 参数无效
    RPCInternalError,        # -32603: 内部错误
    RPCServerError,          # -32000 ~ -32099: 服务器自定义错误
)
```

### 10.2 方法内抛出异常

```python
from okstdio.general.errors import RPCInvalidParamsError, RPCServerError

@app.add_method()
def get_user(user_id: int) -> dict:
    if user_id <= 0:
        raise RPCInvalidParamsError("user_id 必须大于 0")
    user = db.find(user_id)
    if not user:
        raise RPCServerError("用户不存在", code=-32001)
    return user.dict()
```

### 10.3 返回错误响应

```python
from okstdio.general.jsonrpc_model import JSONRPCServerErrorDetail

@app.add_method()
def restricted_action() -> dict | JSONRPCServerErrorDetail:
    if not check_permission():
        return JSONRPCServerErrorDetail(
            code=-32001,
            message="权限不足",
            data={"required": "admin"}
        )
    return {"status": "ok"}
```

### 10.4 客户端错误处理

```python
from okstdio.general.errors import RPCError

# 方式一：检查响应
response = await future
if hasattr(response, 'error'):
    print(f"错误: {response.error.message}")
else:
    print(f"成功: {response.result}")

# 方式二：RPCFuture 的 .error() 回调
await client.call("method", {}).then(
    lambda result: print(result)
).error(
    lambda err: print(f"出错: {err}")
)

# 方式三：try/except
try:
    response = await client.call("method", {})
except RPCError as e:
    print(f"RPC 错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 11. TUI 调试工具

### 11.1 启动

```bash
# 模块路径
rcptui --server tests.test_server

# 脚本路径
rcptui --server path/to/server.py

# 使用 uv
uv run rcptui --server tests.test_server
```

### 11.2 界面说明

```
┌──────────────────────────────────────────────────────────────────┐
│ OkStdio TUI - tests.test_server                                  │
├───────────────────┬──────────────────────────────────────────────┤
│ Method Tree       │ Method: hello [问候]                         │
│                   ├──────────────────────────────────────────────┤
│ ▼ my_server       │ Params (JSON):                               │
│ ├── ping          │ {                                            │
│ ├── hello         │   "name": "string"                           │
│ └── ▶ user        │ }                                            │
│    ├── create     ├──────────────────────────────────────────────┤
│    └── delete     │ [Response] [Log]                             │
│                   ├──────────────────────────────────────────────┤
│                   │ {                                            │
│                   │   "result": "Hello, World!"                  │
│                   │ }                                            │
├───────────────────┴──────────────────────────────────────────────┤
│ Ctrl+j 发送 | Ctrl+r 重启 | Ctrl+l 清日志 | Ctrl+q 退出          │
└──────────────────────────────────────────────────────────────────┘
```

### 11.3 使用流程

1. 启动 `rcptui` 并指定服务器路径
2. 等待服务器连接（自动完成）
3. 在左侧方法树中用方向键选择方法
4. 参数编辑器自动生成参数模板
5. 按需修改参数（标准 JSON 格式）
6. 按 `Ctrl+j` 发送请求
7. 在 Response 标签页查看结果
8. 切换到 Log 标签页查看历史记录

### 11.4 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+j` | 发送请求 |
| `Ctrl+r` | 重启服务器进程 |
| `Ctrl+l` | 清理日志 |
| `Ctrl+q` | 退出 |

---

## 12. 自动文档生成

### 12.1 生成 Markdown 文档

```python
if __name__ == "__main__":
    app.docs_markdown()   # 生成 {server_name}.md
    app.runserver()
```

生成内容：
- 服务器信息（名称、版本、标签）
- 所有方法的签名、参数、返回值
- Pydantic 模型的字段说明
- 中间件列表
- 路由器结构

### 12.2 获取方法树（JSON）

```python
# 服务器端
method_tree = app.get_method_tree()

# 客户端
method_tree = await client.get_server_methods()
```

方法树结构：

```json
{
  "server_name": "my_server",
  "version": "v1.0.0",
  "label": "我的服务器",
  "methods": [
    {
      "name": "hello",
      "label": "问候",
      "path": "my_server.hello",
      "doc": "向用户发出问候",
      "params": [...],
      "results": [...]
    }
  ],
  "middlewares": [...],
  "routers": {
    "user": {
      "prefix": "user",
      "label": "用户管理",
      "methods": [...],
      "routers": {}
    }
  }
}
```

---

## 13. 最佳实践

### 13.1 日志配置（重要）

确保日志只写入文件，**不能输出到 stdout**，否则会干扰 JSON-RPC 通信：

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "app.log",
    maxBytes=2 * 1024 * 1024,  # 2MB
    backupCount=5,
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()  # 移除默认 handler（包括 StreamHandler）
root_logger.addHandler(handler)
```

### 13.2 服务器模块结构推荐

```python
# server.py
import logging
from logging.handlers import RotatingFileHandler
from okstdio.server import RPCServer, IOWrite

# 日志配置（在所有导入后、服务器创建前）
handler = RotatingFileHandler("server.log", maxBytes=2*1024*1024, encoding="utf-8")
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(handler)

app = RPCServer("my_server", label="服务器", version="v1.0.0")

@app.add_method()
def ping() -> str:
    return "pong"

if __name__ == "__main__":
    app.runserver()
```

### 13.3 使用 Pydantic 模型管理复杂参数

```python
class CreateOrderParams(BaseModel):
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., ge=1, le=100)
    address: str = Field(..., min_length=10)

class OrderResult(BaseModel):
    order_id: str
    status: str
    total: float

@app.add_method(name="create_order")
def create_order(params: CreateOrderParams) -> OrderResult:
    return OrderResult(
        order_id="ORD-001",
        status="pending",
        total=params.quantity * 9.9
    )
```

### 13.4 长任务进度推送模式

```python
# 服务器端
@app.add_method()
async def process_files(files: list[str], io_write: IOWrite) -> dict:
    total = len(files)
    for i, file in enumerate(files):
        # 处理文件...
        await io_write.write({
            "type": "progress",
            "current": i + 1,
            "total": total,
            "file": file
        })
    return {"processed": total}

# 客户端
async with client.stream("task_id") as listener:
    future = await client.send(
        "server.process_files",
        {"files": ["a.txt", "b.txt"], "task_id": "task_id"}
    )
    async for msg in listener:
        print(f"进度 {msg['current']}/{msg['total']}: {msg['file']}")
    result = await future
    print(f"完成: {result.result}")
```

### 13.5 多服务器协作模式

```python
from okstdio import ClientManager

async def process_with_multiple_servers():
    async with ClientManager() as manager:
        await manager.add("ocr", "services.ocr_server")
        await manager.add("nlp", "services.nlp_server")
        await manager.add("db", "services.db_server")
        await manager.start_all()

        # 串行调用
        ocr_result = await manager.send_to("ocr", "extract_text", {"image": "..."})
        text = (await ocr_result).result

        nlp_result = await manager.send_to("nlp", "analyze", {"text": text})
        analysis = (await nlp_result).result

        await manager.send_to("db", "save", {"data": analysis})

        # 广播健康检查
        health_results = await manager.broadcast("health_check", {})
        for r in health_results:
            print(f"{r.client_name}: {'OK' if not r.error else 'FAIL'}")
```

---

## 14. API 参考

### RPCServer

```python
class RPCServer(server_name: str = "app", label: str = "", version: str = "v0.1.0")
```

| 方法 | 说明 |
|------|------|
| `add_method(name, label)` | 装饰器，注册 RPC 方法 |
| `add_middleware(label)` | 装饰器，注册中间件 |
| `include_router(router)` | 挂载路由器 |
| `register_dependency(key, factory, singleton)` | 注册依赖 |
| `get_dependency(key)` | 获取依赖实例 |
| `has_dependency(key)` | 检查依赖是否存在 |
| `get_method_tree()` | 获取方法树（dict） |
| `docs_markdown()` | 生成 Markdown 文档 |
| `runserver()` | 启动服务器（阻塞） |

### RPCClient

```python
class RPCClient(name: str)
```

| 方法 | 说明 |
|------|------|
| `start(app, *extra_args)` | 启动服务器子进程 |
| `stop()` | 停止客户端 |
| `send(method, params, request_id)` | 发送请求，返回 Future |
| `call(method, params, request_id, timeout)` | 发送请求，返回 RPCFuture |
| `stream(listen_id, timeout)` | 返回流式监听上下文管理器 |
| `add_listen_queue(listen_id)` | 添加监听队列 |
| `del_listen_queue(listen_id)` | 删除监听队列 |
| `get_server_methods()` | 获取服务器方法树 |

### RPCFuture

| 方法 | 说明 |
|------|------|
| `then(handler, extra_params, create_task)` | 注册成功回调 |
| `error(handler)` | 注册错误回调 |
| `__await__()` | 可直接 await，返回 JSONRPCResponse |

### ClientManager

```python
class ClientManager()
```

| 方法 | 说明 |
|------|------|
| `add(client_name, app, *extra_args)` | 创建并添加客户端 |
| `add_client(client)` | 添加已有客户端 |
| `remove(client_name)` | 移除客户端 |
| `remove_and_stop(client_name)` | 移除并停止客户端 |
| `get(client_name)` | 获取客户端 |
| `start_all()` | 并发启动所有客户端 |
| `stop_all()` | 并发停止所有客户端 |
| `send_to(client_name, method, params)` | 向指定客户端发送 |
| `call_to(client_name, method, params, timeout)` | 链式调用指定客户端 |
| `broadcast(method, params, targets, timeout)` | 广播请求 |
| `clients` | 所有客户端字典 |
| `client_names` | 客户端名称列表 |

### IOWrite

| 方法 | 说明 |
|------|------|
| `write(response)` | 推送消息到父进程（异步），接受 `dict` 或 `JSONRPCResponse` |

### Inject

```python
from okstdio import Inject
# 或
from okstdio.server import Inject
```

标记类，配合 `typing.Annotated` 使用，将参数声明为依赖注入，使其从 API 文档和 TUI 调试器中排除：

```python
def my_method(dep: Annotated[MyDep, Inject()], normal_param: str) -> dict: ...
```

### RPCRouter

```python
class RPCRouter(prefix: str, label: str = "")
```

| 方法 | 说明 |
|------|------|
| `add_method(name, label)` | 装饰器，注册方法 |
| `add_middleware(label)` | 装饰器，注册中间件 |
| `include_router(router)` | 挂载子路由器 |

---

*文档版本：1.0.0 | 更新日期：2026-03-08*
