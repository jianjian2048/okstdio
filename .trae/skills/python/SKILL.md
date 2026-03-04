---
name: python
description: |
  Python 软件开发全栈指南。涵盖项目配置、包管理、CLI 开发和流行库。
  适用于：Python 项目设置、选择 Python 工具、理解 Python 语言特性、虚拟环境、类型注解、异步编程、打包策略
  不适用于：特定工具深度指南（使用子技能：project-system、package-management、cli、packages）
license: MIT
metadata:
  displayName: "Python"
  author: "Tyler-R-Kendrick"
  version: "1.0.0"
  tags:
    - python
    - pip
    - uv
    - poetry
    - pyproject
    - cli
compatibility: claude, copilot, cursor
references:
  - title: "Python 官方文档"
    url: "https://docs.python.org/3/"
  - title: "CPython GitHub 仓库"
    url: "https://github.com/python/cpython"
  - title: "Python 打包用户指南"
    url: "https://packaging.python.org/en/latest/"
---

# Python 技能树

涵盖 Python 软件开发全栈指南，包括项目配置、依赖管理、CLI 工具和现代 Python 生态系统中的最佳实践。

## 概述

Python 是最广泛使用的编程语言之一，驱动着 Web 后端、数据科学、机器学习、DevOps 自动化、CLI 工具和脚本。近年来，Python 生态系统经历了重大现代化，`pyproject.toml` 取代了 `setup.py`，类型注解成为标准，`uv` 等新型高性能工具正在改变开发者体验。

本技能树提供了有效导航 Python 生态系统的结构化指南。

## 知识地图

```
python/
  project-system/       pyproject.toml、构建后端、setuptools、hatch、flit、maturin
  package-management/   pip、uv、poetry、pdm、conda、pipx、虚拟环境
  cli/                  argparse、click、typer、rich、textual
  packages/             流行库和框架（Flask、FastAPI、Django、pytest 等）
```

## 子技能分类

| 类别 | 子技能 | 覆盖内容 |
|----------|-----------|----------------|
| **项目系统** | `project-system` | `pyproject.toml` 结构、构建后端（setuptools、hatchling、flit-core、maturin）、PEP 517/518/621/660、入口点、版本控制、发布 |
| **包管理** | `package-management` | pip、uv、poetry、pdm、conda、pipx、虚拟环境、锁文件、私有索引 |
| **CLI 开发** | `cli` | argparse、click、typer、rich、textual、输出格式化、CLI 应用测试 |
| **包** | `packages` | 用于 Web、数据、测试等的流行 Python 库和框架 |

## 选择指南

| 我需要... | 使用此子技能 |
|---|---|
| 使用 `pyproject.toml` 设置新 Python 项目 | `project-system` |
| 在 setuptools、hatch、flit 或 poetry 之间选择构建工具 | `project-system` |
| 配置入口点或控制台脚本 | `project-system` |
| 将包发布到 PyPI | `project-system` |
| 安装依赖或管理锁文件 | `package-management` |
| 在 pip、uv、poetry、pdm 或 conda 之间选择 | `package-management` |
| 设置虚拟环境 | `package-management` |
| 配置私有包索引 | `package-management` |
| 构建命令行应用 | `cli` |
| 添加丰富的终端输出（颜色、表格、进度条） | `cli` |
| 构建终端 UI（TUI） | `cli` |
| 在 argparse、click 和 typer 之间选择 | `cli` |

## Python 版本概览

| 版本 | 状态 | 主要特性 |
|---------|--------|--------------|
| **3.9** | 安全修复 | 字典合并运算符（`\|`、`\|=`）、`str.removeprefix()`/`removesuffix()`、标准集合中的类型注解泛型 |
| **3.10** | 安全修复 | 结构化模式匹配（`match`/`case`）、括号上下文管理器、`TypeAlias`、更好的错误消息 |
| **3.11** | 维护中 | 异常组和 `except*`、stdlib 中的 `tomllib`、显著性能改进（快 10-60%）、用于 asyncio 的 `TaskGroup` |
| **3.12** | 维护中 | 类型参数语法（`type X = ...`）、f-string 改进、每个解释器的 GIL（子解释器）、`pathlib` 改进 |
| **3.13** | 最新稳定版 | 自由线程模式（实验性、无 GIL）、JIT 编译器（实验性）、改进的 `typing` 模块、更好的 REPL |
| **3.14+** | 开发中 | 延迟注解求值（PEP 649）、进一步的 JIT/自由线程改进 |

**建议**：新项目目标 Python 3.11+。如果需要新的类型参数语法，请使用 3.12+。使用 3.13 来实验自由线程模式。

## 核心语言特性快速参考

### 类型注解（PEP 484、526、604、612、695）

```python
# 基本类型注解
def greet(name: str) -> str:
    return f"Hello, {name}"

# 泛型集合（3.9+ -- 无需 typing.List、typing.Dict）
def process(items: list[int]) -> dict[str, int]:
    return {str(i): i for i in items}

# 联合类型（3.10+ -- 使用 | 而非 Union）
def parse(value: str | int) -> str:
    return str(value)

# Optional 是 X | None 的简写
def find(key: str) -> str | None:
    ...

# TypeVar 和泛型（3.12+ 类型参数语法）
type Comparable = int | float | str

def maximum[T: Comparable](a: T, b: T) -> T:
    return a if a >= b else b

# TypedDict 用于结构化字典
from typing import TypedDict

class UserConfig(TypedDict):
    name: str
    age: int
    email: str | None
```

### 异步/等待（PEP 492）

```python
import asyncio

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# TaskGroup（3.11+）-- 结构化并发
async def fetch_all(urls: list[str]) -> list[dict]:
    results = []
    async with asyncio.TaskGroup() as tg:
        for url in urls:
            tg.create_task(fetch_data(url))
    return results

# 异步生成器
async def stream_lines(path: str):
    async with aiofiles.open(path) as f:
        async for line in f:
            yield line.strip()
```

### 数据类（PEP 557）

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    tags: list[str] = field(default_factory=list)

# 冻结（不可变）数据类
@dataclass(frozen=True)
class Point:
    x: float
    y: float

# Slots 用于内存效率（3.10+）
@dataclass(slots=True)
class Measurement:
    timestamp: float
    value: float
    unit: str
```

### 模式匹配（PEP 634、3.10+）

```python
def handle_command(command: dict) -> str:
    match command:
        case {"action": "quit"}:
            return "Goodbye"
        case {"action": "greet", "name": str(name)}:
            return f"Hello, {name}"
        case {"action": "move", "x": int(x), "y": int(y)} if x > 0:
            return f"Moving right to ({x}, {y})"
        case _:
            return "Unknown command"
```

### 异常组（PEP 654、3.11+）

```python
# 抛出多个异常
def validate(data: dict) -> None:
    errors = []
    if "name" not in data:
        errors.append(ValueError("Missing name"))
    if "age" not in data:
        errors.append(ValueError("Missing age"))
    if errors:
        raise ExceptionGroup("Validation failed", errors)

# 处理异常组
try:
    validate({})
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"Validation error: {exc}")
except* TypeError as eg:
    for exc in eg.exceptions:
        print(f"Type error: {exc}")
```

### 上下文管理器

```python
from contextlib import contextmanager, asynccontextmanager

@contextmanager
def managed_resource(name: str):
    print(f"Acquiring {name}")
    try:
        yield name
    finally:
        print(f"Releasing {name}")

# 括号上下文管理器（3.10+）
with (
    open("input.txt") as fin,
    open("output.txt", "w") as fout,
):
    fout.write(fin.read())
```

## 最佳实践

### 始终使用虚拟环境

永远不要将项目依赖安装到系统 Python 中。使用 `venv`、`uv venv`，或让包管理器（poetry、pdm）处理环境创建。

```bash
# 标准库
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 使用 uv（更快）
uv venv
source .venv/bin/activate
```

### 采用类型注解

在整个代码库中使用类型注解。它们提高可读性、启用 IDE 支持，并通过 `mypy` 或 `pyright` 及早捕获错误。

```bash
# 使用 mypy 进行类型检查
pip install mypy
mypy src/

# 使用 pyright 进行类型检查（更快，VS Code 中的 Pylance 使用）
pip install pyright
pyright src/
```

### 使用 Ruff 进行格式化和 linting

Ruff 是用 Rust 编写的极快 Python linter 和格式化器。它取代了 flake8、isort、black 和许多其他工具。

```bash
# 安装
pip install ruff

# Lint
ruff check src/

# 格式化（取代 black）
ruff format src/

# 修复自动修复问题
ruff check --fix src/
```

`pyproject.toml` 中的最小 `ruff` 配置：

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle 错误
    "W",    # pycodestyle 警告
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
]

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]
```

### 使用 `pyproject.toml` 进行所有配置

将工具配置整合在 `pyproject.toml` 中，而不是分散在 `setup.cfg`、`tox.ini`、`.flake8` 等文件中。

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.coverage.run]
source = ["src"]
branch = true
```

### 使用 pytest 编写测试

使用 `pytest` 作为测试运行器。它是 Python 生态系统中的事实标准。

```bash
pip install pytest pytest-cov

# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=src --cov-report=term-missing
```

### 使用 `__all__` 控制公共 API

在 `__init__.py` 文件中定义 `__all__` 以明确公共 API：

```python
# src/mypackage/__init__.py
__all__ = ["Client", "Config", "process_data"]

from .client import Client
from .config import Config
from .processing import process_data
```
