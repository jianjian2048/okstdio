# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

OkStdio 是一个基于 Stdio 的 JSON-RPC 父子进程通信框架，支持完整的 JSON-RPC 2.0 协议规范。

## 常用命令

```bash
# 构建包
uv build

# 发布到 PyPI
uv publish

# 发布到 Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/

# 运行示例客户端（会自动启动服务器）
python -m example.client

# 单独运行服务器（生成 API 文档并启动）
python -m example.server
```

## 架构结构

### 代码目录

- `src/okstdio/` - 核心库源码
  - `server/` - 服务器端实现
  - `client/` - 客户端实现
  - `general/` - JSON-RPC 协议模型和错误定义
- `example/` - 完整的示例项目（英雄管理系统）

### 核心组件

**服务器端 (`src/okstdio/server/`)**:
- `application.py` - RPCServer 主类，处理请求分发和方法执行
- `router.py` - RPCRouter 路由系统，支持方法前缀和嵌套路由
- `middleware.py` - 中间件管理机制
- `stream.py` - Stdio 流读写封装
- `appdoc.py` - 自动生成 Markdown API 文档

**客户端 (`src/okstdio/client/`)**:
- `application.py` - RPCClient 主类，管理子进程生命周期和请求发送

**协议层 (`src/okstdio/general/`)**:
- `jsonrpc_model.py` - JSON-RPC 2.0 数据模型（Pydantic）
- `errors.py` - 标准错误类型定义

### 通信流程

```
客户端 (RPCClient)          服务器端 (RPCServer)
     |                              |
     |-- 启动子进程 (stdin/stdout) ->|
     |                              |
     |-- JSON-RPC 请求 (stdout) ---->|
     |                              |-- 路由分发
     |                              |-- 中间件处理
     |                              |-- 方法执行
     |<-- 响应 (stdin) --------------|
     |                              |
     |<-- 流式推送 (IOWrite) --------| (可选)
```

### 关键特性

1. **路由系统**: 支持点分隔的路由路径（如 `hero.create`），自动处理前缀匹配
2. **中间件链**: 请求依次通过中间件处理，支持拦截和修改请求/响应
3. **流式响应**: 通过 `IOWrite` 依赖注入实现服务器主动推送
4. **类型验证**: 基于 Pydantic 的参数验证和序列化
5. **编码处理**: Windows 平台自动处理 UTF-8 编码

### 示例项目结构

`example/` 目录展示了完整的使用场景:
- `server.py` - 英雄管理服务器，包含 CRUD 操作和副本战斗系统
- `client.py` - 客户端交互示例
- `schemas.py` - Pydantic 数据模型定义
- `databases.py` - SQLite 数据库持久化
