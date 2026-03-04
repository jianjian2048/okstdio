---
name: project-system
description: |
  使用 pyproject.toml、构建后端和现代 PEP 标准进行 Python 项目配置和打包的指南。
  适用于：创建 pyproject.toml、配置构建后端（setuptools、hatchling、flit-core、maturin、poetry-core、pdm-backend）、入口点、版本管理、发布到 PyPI、可编辑安装、monorepo 模式
  不适用于：安装包或运行时管理依赖（使用 package-management）、构建 CLI 应用（使用 cli）
license: MIT
metadata:
  displayName: "Python 项目系统"
  author: "Tyler-R-Kendrick"
  version: "1.0.0"
  tags:
    - python
    - pyproject
    - setuptools
    - hatch
    - flit
    - maturin
    - packaging
    - pep621
compatibility: claude, copilot, cursor
references:
  - title: "Python 打包用户指南 - pyproject.toml"
    url: "https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
  - title: "PEP 621 - 在 pyproject.toml 中存储项目元数据"
    url: "https://peps.python.org/pep-0621/"
  - title: "Setuptools 文档"
    url: "https://setuptools.pypa.io/en/latest/"
---

# Python 项目系统

## 概述

现代 Python 打包已统一使用 `pyproject.toml` 作为项目元数据、构建配置和工具设置的单一数据源。一系列 PEP 已标准化 Python 项目的构建、分发和安装方式：

| PEP | 标题 | 影响 |
|-----|-------|--------|
| **PEP 517** | 构建系统接口 | 定义前端（pip、build）如何调用后端（setuptools、hatchling） |
| **PEP 518** | 构建系统要求 | 在 `pyproject.toml` 中引入 `[build-system]` 表 |
| **PEP 621** | 项目元数据 | 标准化 `[project]` 表用于名称、版本、依赖等 |
| **PEP 660** | 可编辑安装 | 为 PEP 517 后端标准化 `pip install -e .` |
| **PEP 639** | 许可证元数据 | 引入 `license-files` 和 SPDX 许可证表达式 |
| **PEP 723** | 内联脚本元数据 | 允许单文件脚本声明依赖 |

关键洞察：**构建后端现在是可插拔的**。您在 `[build-system]` 中选择后端，在 `[project]` 中定义元数据，任何 PEP 517 兼容的前端（pip、build、uv）都可以构建您的包。

## pyproject.toml 结构

完整的注释 `pyproject.toml`：

```toml
# ============================================================
# 构建系统（PEP 518）
# 告诉 pip/build 使用哪个后端以及首先安装什么
# ============================================================
[build-system]
requires = ["hatchling"]            # 构建依赖
build-backend = "hatchling.build"   # 后端的入口点

# ============================================================
# 项目元数据（PEP 621）
# 所有后端都能理解的标准化元数据
# ============================================================
[project]
name = "my-package"
version = "1.2.0"                   # 静态版本（或使用下面的动态版本）
description = "包的简短摘要"
readme = "README.md"
license = "MIT"                     # SPDX 表达式（PEP 639）
requires-python = ">=3.11"
authors = [
    { name = "Jane Doe", email = "jane@example.com" },
]
maintainers = [
    { name = "Team Lead", email = "lead@example.com" },
]
keywords = ["automation", "tooling"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Typing :: Typed",
]

# 核心依赖
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0,<3",
    "rich>=13.0",
]

# ============================================================
# 可选依赖组
# 安装方式：pip install my-package[dev]
# ============================================================
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "ruff>=0.5",
]
docs = [
    "sphinx>=7.0",
    "sphinx-rtd-theme>=2.0",
]

# ============================================================
# 入口点
# ============================================================
[project.scripts]
my-cli = "my_package.cli:main"         # 控制台脚本

[project.gui-scripts]
my-gui = "my_package.gui:launch"       # GUI 脚本（Windows 上无控制台窗口）

[project.entry-points."my_package.plugins"]
builtin = "my_package.plugins.builtin:BuiltinPlugin"  # 插件入口点组

# ============================================================
# PyPI 上显示的 URL
# ============================================================
[project.urls]
Homepage = "https://github.com/example/my-package"
Documentation = "https://my-package.readthedocs.io"
Repository = "https://github.com/example/my-package"
Issues = "https://github.com/example/my-package/issues"
Changelog = "https://github.com/example/my-package/blob/main/CHANGELOG.md"

# ============================================================
# 后端特定配置
# （此部分因后端而异 - 示例为 hatchling）
# ============================================================
[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]

# ============================================================
# 工具配置（pytest、mypy、ruff、coverage 等）
# ============================================================
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q --strict-markers"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM"]

[tool.coverage.run]
source = ["src/my_package"]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = 80
```

## 构建后端比较

| 后端 | 包 | 优势 | 最适合 |
|---------|---------|-----------|----------|
| **setuptools** | `setuptools` | 最成熟，庞大生态系统，支持 C 扩展 | 旧项目、C 扩展、最大兼容性 |
| **hatchling** | `hatchling` | 快速、现代、优秀默认设置、Hatch 项目管理器 | 新纯 Python 项目、想要完整工作流工具的项目 |
| **flit-core** | `flit-core` | 最小化和简单、非常快速的构建 | 无特殊构建步骤的简单纯 Python 包 |
| **pdm-backend** | `pdm-backend` | PEP 621 原生、支持 PEP 582 | 使用 pdm 作为包管理器的项目 |
| **maturin** | `maturin` | 构建 Rust+Python（PyO3/cffi）包 | Rust 扩展、高性能编译模块 |
| **poetry-core** | `poetry-core` | 与 Poetry 工作流集成 | 已使用 Poetry 的项目（注意：某些字段使用 `[tool.poetry]` 而非 `[project]`） |

### 按后端的构建系统配置

**setuptools**（最常见、最灵活）：
```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**hatchling**（推荐用于新项目）：
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**flit-core**（最小化）：
```toml
[build-system]
requires = ["flit_core>=3.9"]
build-backend = "flit_core.buildapi"
```

**pdm-backend**：
```toml
[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"
```

**maturin**（Rust 扩展）：
```toml
[build-system]
requires = ["maturin>=1.7"]
build-backend = "maturin"
```

**poetry-core**：
```toml
[build-system]
requires = ["poetry-core>=1.9"]
build-backend = "poetry.core.masonry.api"
```

## 源码布局与平面布局

### 源码布局（推荐）

```
my-package/
  pyproject.toml
  README.md
  LICENSE
  src/
    my_package/
      __init__.py
      core.py
      utils.py
  tests/
    __init__.py
    test_core.py
    test_utils.py
```

**优势**：
- 防止意外导入开发版本（强制安装）
- 源代码和项目元数据之间的清晰分离
- 避免包目录和测试/脚本导入之间的名称冲突
- 某些后端（flit）默认需要

**setuptools 配置**用于 src 布局：
```toml
[tool.setuptools.packages.find]
where = ["src"]
```

**hatchling 配置**用于 src 布局：
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
```

### 平面布局

```
my-package/
  pyproject.toml
  README.md
  LICENSE
  my_package/
    __init__.py
    core.py
    utils.py
  tests/
    test_core.py
```

**优势**：
- 更简单的目录结构
- 开发期间导入路径中无 `src/` 前缀
- 与大多数后端开箱即用

**setuptools 配置**用于平面布局：
```toml
[tool.setuptools.packages.find]
include = ["my_package*"]
```

**建议**：对于发布到 PyPI 的库和包使用 **源码布局**。对于不会作为包分发的应用和脚本使用 **平面布局**。

## 入口点

### 控制台脚本

控制台脚本创建可执行命令，安装到用户的 PATH 中：

```toml
[project.scripts]
my-cli = "my_package.cli:main"
my-tool = "my_package.tools:run"
```

格式为 `command-name = "module.path:function"`。函数无参数调用。

```python
# src/my_package/cli.py
import sys

def main() -> int:
    """my-cli 命令的入口点。"""
    print("Hello from my-cli!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### GUI 脚本

与控制台脚本相同，但在 Windows 上不打开控制台窗口：

```toml
[project.gui-scripts]
my-gui = "my_package.gui:launch"
```

### 插件入口点组

用于第三方包可以注册扩展的插件系统：

```toml
# 在插件包的 pyproject.toml 中
[project.entry-points."myapp.plugins"]
csv-export = "myapp_csv:CsvExporter"
json-export = "myapp_json:JsonExporter"
```

运行时发现插件：

```python
from importlib.metadata import entry_points

def load_plugins():
    eps = entry_points(group="myapp.plugins")
    plugins = {}
    for ep in eps:
        plugins[ep.name] = ep.load()
    return plugins
```

## 版本管理策略

### 静态版本控制

直接在 `pyproject.toml` 中定义版本：

```toml
[project]
version = "1.2.0"
```

在每次发布前手动更新。简单但容易出错。

### 从 Python 文件动态版本控制

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "my_package.__version__"}
```

```python
# src/my_package/__init__.py
__version__ = "1.2.0"
```

### 使用 setuptools-scm 的 SCM 基于版本控制

从 git 标签自动派生版本：

```toml
[build-system]
requires = ["setuptools>=75.0", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[project]
dynamic = ["version"]

[tool.setuptools_scm]
# 版本从最新 git 标签派生
# 标签 "v1.2.0" -> 版本 "1.2.0"
# 标签后 3 次提交 -> 版本 "1.2.1.dev3+g1234abc"
```

工作流：
```bash
git tag v1.0.0
git push --tags
# 版本现在是 1.0.0

# 在没有标签的更多提交后：
# 版本变为 1.0.1.dev3+g1234abc
```

### Hatch 版本管理

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
path = "src/my_package/__about__.py"
```

```python
# src/my_package/__about__.py
__version__ = "1.2.0"
```

使用 CLI 升级：
```bash
hatch version minor   # 1.2.0 -> 1.3.0
hatch version patch   # 1.3.0 -> 1.3.1
hatch version major   # 1.3.1 -> 2.0.0
```

## 包发现配置

### setuptools 自动发现

```toml
# 查找 src/ 下的所有包
[tool.setuptools.packages.find]
where = ["src"]

# 排除测试包
[tool.setuptools.packages.find]
where = ["src"]
exclude = ["tests*"]
```

### 包含数据文件

```toml
# setuptools
[tool.setuptools.package-data]
my_package = ["data/*.json", "templates/*.html"]

# hatchling
[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]

[tool.hatch.build.targets.wheel.force-include]
"config/defaults.json" = "my_package/defaults.json"
```

### 从 SDist 包含或排除文件

```toml
# hatchling
[tool.hatch.build.targets.sdist]
include = ["src/", "tests/", "README.md", "LICENSE"]
exclude = ["*.pyc", "__pycache__"]

# setuptools -- 使用 MANIFEST.in
# include src/my_package/data/*.json
# exclude tests/*
```

## 构建和发布工作流

### 构建分发包

使用标准 `build` 工具（PEP 517 前端）：

```bash
# 安装 build 工具
pip install build

# 构建 sdist 和 wheel
python -m build

# 输出到 dist/
# dist/my_package-1.2.0.tar.gz      (sdist)
# dist/my_package-1.2.0-py3-none-any.whl  (wheel)
```

### 发布到 PyPI

**使用 twine**（传统）：

```bash
pip install twine

# 首先上传到 Test PyPI
twine upload --repository testpypi dist/*

# 上传到生产 PyPI
twine upload dist/*
```

**使用可信发布者**（推荐用于 CI/CD）：

可信发布通过 CI 提供商的 OIDC 身份消除 API 令牌。在 PyPI 上配置：

1. 转到 PyPI 项目设置并添加"可信发布者"
2. 配置您的 CI 提供商（GitHub Actions、GitLab CI 等）
3. 无需密钥或令牌

GitHub Actions 示例：

```yaml
name: 发布到 PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write  # 可信发布所需

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # 无需令牌 -- 使用 OIDC
```

**使用 uv publish**（现代替代）：

```bash
uv publish
# 或发布到 Test PyPI
uv publish --index-url https://test.pypi.org/legacy/
```

## 可编辑安装（PEP 660）

可编辑安装让您在每次更改后无需重新安装即可开发包：

```bash
# 标准可编辑安装
pip install -e .

# 带可选依赖
pip install -e ".[dev,docs]"

# 使用 uv
uv pip install -e .
```

**工作原理**：后端创建特殊的 `.pth` 文件或导入钩子，将导入重定向到源目录。源文件的更改立即生效。

**后端支持**：
- setuptools：完全支持（使用导入钩子或 `.pth` 文件）
- hatchling：完全支持
- flit：完全支持
- pdm-backend：完全支持
- maturin：支持（使用 `maturin develop` 在导入时重建 Rust 代码）

## Monorepo 模式

### 多包工作区

```
monorepo/
  pyproject.toml          # 根项目（可选，用于工作区工具）
  packages/
    core/
      pyproject.toml
      src/core/
        __init__.py
    api/
      pyproject.toml
      src/api/
        __init__.py
    cli/
      pyproject.toml
      src/cli/
        __init__.py
```

### 包间依赖

开发期间通过路径引用兄弟包：

```toml
# packages/api/pyproject.toml
[project]
dependencies = [
    "core",  # 用于从 PyPI 安装的发布名称
]

# 用于本地开发，安装：
# pip install -e packages/core
# pip install -e packages/api
```

### uv 工作区

uv 支持原生工作区管理：

```toml
# 根 pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
```

```bash
# 以可编辑模式安装所有工作区成员
uv sync
```

### Hatch 工作区

```toml
# 根 pyproject.toml
[tool.hatch.envs.default]
dependencies = [
    "core @ {root:uri}/packages/core",
    "api @ {root:uri}/packages/api",
]
```

## 最佳实践

1. **始终使用 `pyproject.toml`**。不要创建新的 `setup.py` 或 `setup.cfg` 文件。这些是旧版。

2. **库选择源码布局**。防止导入混淆，是发布包的社区标准。

3. **在 `[build-system].requires` 中固定构建后端版本**以避免意外：
   ```toml
   requires = ["hatchling>=1.25,<2"]
   ```

4. **使用 `requires-python`** 声明最低 Python 版本：
   ```toml
   requires-python = ">=3.11"
   ```

5. **指定依赖边界**。使用 `>=` 的最低版本和可选上限：
   ```toml
   dependencies = [
       "httpx>=0.27",
       "pydantic>=2.0,<3",
   ]
   ```

6. **使用可选依赖组**进行开发、测试和文档依赖，以保持核心包精简。

7. **为类型化包包含 `py.typed` 标记**：
   ```
   src/my_package/py.typed   # 空文件 -- 表示 PEP 561 合规
   ```

8. **对库使用基于 SCM 的版本控制**（setuptools-scm）以避免手动版本升级。

9. **发布前测试您的打包**：
   ```bash
   python -m build
   twine check dist/*
   pip install dist/*.whl
   ```

10. **从 CI/CD 上传 PyPI 时使用可信发布者**，而不是长期 API 令牌。
