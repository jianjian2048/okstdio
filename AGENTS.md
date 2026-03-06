# AGENTS.md

## 项目背景

**okstdio-enhance** 是 [okstdio](https://github.com/jianjian2048/okstdio) 项目的增强分支。

**okstdio** 是一个基于 Stdio 的 JSON-RPC 父子进程通信框架，提供了：
- JSON-RPC 2.0 协议实现
- 异步通信支持
- 中间件机制
- 自动文档生成
- 流式响应支持

## 项目定位

okstdio-enhance 的目标是在 okstdio 的基础上增加功能，使框架更加健壮。

### 已实现的增强功能

#### 依赖注入系统 (v0.1.0+)
- ✅ 灵活的依赖注册和管理机制
- ✅ 支持类型键和字符串键
- ✅ 单例/非单例生命周期管理
- ✅ 运行时动态注册依赖
- ✅ 内置 IOWrite 依赖自动注册
- ✅ 线程安全的依赖创建

#### 服务器方法树功能 (v0.1.0+)
- ✅ 自动注册 `__system__` 系统方法
- ✅ 支持获取完整的服务器方法树结构
- ✅ 包含方法、参数、返回值、中间件和路由信息
- ✅ 客户端便捷方法 `get_server_methods()`
- ✅ 系统方法隔离，不经过中间件

#### TUI 调试工具 (v0.1.0+)
- ✅ 可视化方法树浏览
- ✅ 交互式参数编辑（JSON 语法高亮）
- ✅ 请求发送和响应显示
- ✅ 请求/响应日志记录
- ✅ 命令行工具 `rcptui`
- ✅ 基于 Textual 框架构建

## 当前状态

- **基础框架**: 基于 okstdio 0.1.0 版本
- **Python 版本**: >=3.10
- **包管理**: 使用 uv
- **开发状态**: Alpha (0.1.0)
- **核心增强**: 依赖注入系统已实现并测试通过
- **TUI 工具**: rcptui 调试工具已实现

## 技术栈

- Python 3.10+
- Pydantic 2.x
- asyncio
- Textual (TUI 框架)
- uv (包管理器)

## 项目结构

```
okstdio-enhance/
├── src/okstdio/
│   ├── server/
│   │   ├── application.py    # RPCServer 和 IOWrite
│   │   ├── dependencies.py   # 依赖注入容器 (新增)
│   │   ├── router.py         # 路由系统
│   │   ├── middleware.py     # 中间件系统
│   │   ├── appdoc.py         # 文档生成
│   │   └── stream.py         # Stdio 流
│   ├── client/
│   │   └── application.py    # RPCClient
│   ├── tui/
│   │   ├── __init__.py       # TUI 模块入口和 run_app 函数
│   │   ├── app.py            # OkstdioApp 主应用
│   │   ├── oktui.scss        # TUI 样式
│   │   └── widgets/
│   │       ├── __init__.py   # widgets 模块入口
│   │       ├── method_tree.py # 方法树组件
│   │       ├── params_editor.py # 参数编辑器
│   │       └── response_viewer.py # 响应查看器
│   ├── general/
│   │   ├── jsonrpc_model.py  # JSON-RPC 模型
│   │   └── errors.py         # 错误定义
│   └── __init__.py
├── tests/
│   ├── test_server.py        # 测试服务器
│   └── test_client.py        # 测试客户端
├── README.md
├── CLAUDE.md
├── AGENTS.md
└── pyproject.toml
```

## 依赖注入使用示例

### 基本用法
```python
from okstdio.server import RPCServer
import uiautomator2 as u2

app = RPCServer("app")

# 注册设备依赖（单例）
app.register_dependency(u2.Device, lambda: u2.connect(), singleton=True)

@app.add_method()
def click(device: u2.Device) -> dict:
    device.click(0.5, 0.5)
    return {"status": "ok"}
```

### 运行时动态注册
```python
@app.add_method()
def init_device(device_ip: str) -> dict:
    device = u2.connect(device_ip)
    app.register_dependency(u2.Device, lambda: device, singleton=True)
    return {"status": "registered"}
```

### API 参考
- `app.register_dependency(key, factory, singleton=True)`: 注册依赖
- `app.get_dependency(key)`: 获取依赖实例
- `app.has_dependency(key)`: 检查依赖是否已注册





