# Python 包管理

## 概述

Python 包管理已经显著发展。虽然 `pip` 仍然是基础工具，但 `uv`、`poetry` 和 `pdm` 等新工具提供了带有锁文件、虚拟环境管理和更快解析的集成工作流。工具的选择取决于项目复杂性、团队偏好以及您是否需要锁文件支持或 monorepo 管理等功能。

## 工具比较

| 功能 | pip | uv | poetry | pdm | conda | pipx | pip-tools |
|---------|-----|----|--------|-----|-------|------|-----------|
| **安装包** | 是 | 是 | 是 | 是 | 是 | 是（全局 CLI 工具） | 是 |
| **锁文件支持** | 否（使用 pip-tools） | 是（`uv.lock`） | 是（`poetry.lock`） | 是（`pdm.lock`） | 是（`conda-lock`） | N/A | 是（`*.in` 的 `requirements.txt`） |
| **虚拟环境管理** | 否（使用 `venv`） | 是（`uv venv`） | 是（自动创建） | 是（自动创建） | 是（conda 环境） | 是（隔离） | 否 |
| **依赖解析** | 回溯 | SAT 求解器（快速） | SAT 求解器 | SAT 求解器 | SAT 求解器 | N/A | 回溯 |
| **速度** | 中等 | 非常快（Rust） | 中等 | 快 | 慢 | 快 | 中等 |
| **Monorepo/工作区** | 否 | 是（工作区） | 否（有限） | 否 | 否 | 否 | 否 |
| **Python 版本管理** | 否 | 是（`uv python`） | 否 | 否 | 是 | 否 | 否 |
| **PEP 621 原生** | 是 | 是 | 部分 | 是 | N/A | N/A | 是 |
| **私有索引** | 是 | 是 | 是 | 是 | 是（渠道） | 是 | 是 |

**建议**：新项目使用 **uv**。它是最快的工具，支持锁文件，管理虚拟环境和 Python 版本，并且完全 PEP 621 兼容。如果您的团队已经投资于其工作流，请使用 **poetry**。对于带有非 Python 依赖的科学计算，请使用 **conda**。

## pip 基础

pip 是 Python 的默认包安装程序，包含在每个 Python 安装中。

### 基本命令

```bash
# 安装包
pip install httpx

# 安装特定版本
pip install httpx==0.27.0

# 使用版本约束安装
pip install "httpx>=0.27,<1.0"

# 从 requirements 文件安装
pip install -r requirements.txt

# 以可编辑模式安装本地包
pip install -e .

# 安装可选依赖
pip install -e ".[dev,docs]"

# 卸载
pip uninstall httpx

# 列出已安装的包
pip list

# 显示包信息
pip show httpx

# 检查过时的包
pip list --outdated

# 升级包
pip install --upgrade httpx
```

### requirements.txt

固定依赖的传统方式：

```
# requirements.txt -- 生产依赖
httpx==0.27.0
pydantic==2.9.2
rich==13.9.4

# requirements-dev.txt -- 开发依赖
-r requirements.txt
pytest==8.3.3
pytest-cov==5.0.0
mypy==1.13.0
ruff==0.7.4
```

### 约束文件

约束文件限制版本而不需要安装：

```
# constraints.txt
# 如果安装包则确保使用这些版本
urllib3>=2.0,<3
certifi>=2024.0
```

```bash
pip install -r requirements.txt -c constraints.txt
```

### pip 配置

```ini
# pip.conf（Linux: ~/.config/pip/pip.conf，macOS: ~/Library/Application Support/pip/pip.conf）
# pip.ini（Windows: %APPDATA%\pip\pip.ini）
[global]
timeout = 60
index-url = https://pypi.org/simple
trusted-host = pypi.org

[install]
require-virtualenv = true   # 防止意外全局安装
```

## uv 深入

uv 是用 Rust 编写的极快 Python 包管理器。它是 pip、venv、pip-tools 等的即插即用替代品。

### 安装

```bash
# 安装 uv（独立）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 或使用 Homebrew
brew install uv
```

### Python 版本管理

```bash
# 列出可用的 Python 版本
uv python list

# 安装特定 Python 版本
uv python install 3.12

# 将项目固定到特定 Python 版本
uv python pin 3.12
# 创建 .python-version 文件
```

### 虚拟环境管理

```bash
# 创建虚拟环境
uv venv

# 使用特定 Python 版本创建
uv venv --python 3.12

# 激活（与标准 venv 相同）
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

### 包安装（pip 兼容接口）

```bash
# 安装包（比 pip 快 10-100 倍）
uv pip install httpx pydantic rich

# 从 requirements 文件安装
uv pip install -r requirements.txt

# 安装可编辑包
uv pip install -e ".[dev]"

# 从 requirements.in 编译锁文件
uv pip compile requirements.in -o requirements.txt

# 同步环境以完全匹配锁文件
uv pip sync requirements.txt

# 冻结当前环境
uv pip freeze > requirements.txt
```

### 项目管理（uv lock / uv sync / uv run）

uv 具有使用 `pyproject.toml` 并创建跨平台锁文件的内置项目管理：

```bash
# 初始化新项目
uv init my-project
cd my-project

# 添加依赖
uv add httpx
uv add pydantic "rich>=13.0"

# 添加开发依赖
uv add --dev pytest pytest-cov mypy ruff

# 删除依赖
uv remove httpx

# 创建/更新锁文件（uv.lock）
uv lock

# 同步环境以匹配 pyproject.toml + uv.lock
uv sync

# 同步包括开发依赖（默认）
uv sync --all-extras

# 在项目环境中运行命令
uv run python -m pytest
uv run my-cli --help
uv run python script.py
```

### uv 工具管理（替换 pipx）

```bash
# 全局安装 CLI 工具（隔离环境）
uv tool install ruff
uv tool install httpie

# 运行工具而不安装它
uv tool run black --check .
uvx ruff check .    # uvx 是 uv tool run 的简写

# 列出已安装的工具
uv tool list

# 升级工具
uv tool upgrade ruff
```

### uv 工作区（Monorepos）

```toml
# 根 pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
```

```bash
# 同步所有工作区成员
uv sync

# 在特定工作区成员中运行命令
uv run --package api python -m pytest
```

### uv 缓存管理

```bash
# 显示缓存目录
uv cache dir

# 清理缓存
uv cache clean

# 清理未使用的缓存条目
uv cache prune
```

## Poetry 工作流

Poetry 为依赖管理、打包和发布提供了一体化解决方案。

### 安装

```bash
# 推荐：使用官方安装程序
curl -sSL https://install.python-poetry.org | python3 -

# 或使用 pipx
pipx install poetry
```

### 项目生命周期

```bash
# 创建新项目
poetry new my-project
cd my-project

# 或在现有目录中初始化
poetry init

# 添加依赖
poetry add httpx
poetry add pydantic "rich>=13.0"

# 添加开发依赖
poetry add --group dev pytest pytest-cov mypy ruff

# 删除依赖
poetry remove httpx

# 更新依赖（尊重版本约束）
poetry update

# 更新特定包
poetry update httpx

# 生成/更新锁文件而不安装
poetry lock

# 从锁文件安装所有依赖
poetry install

# 不安装开发依赖
poetry install --without dev

# 在虚拟环境中运行命令
poetry run python script.py
poetry run pytest

# 激活虚拟环境
poetry shell

# 显示依赖树
poetry show --tree

# 导出到 requirements.txt（用于 Docker）
poetry export -f requirements.txt -o requirements.txt --without-hashes
```

### poetry.lock

`poetry.lock` 文件固定所有依赖（直接和传递）的确切版本。始终将此文件提交到版本控制。

```bash
# 从头重新生成
poetry lock --no-update

# 检查锁文件是否最新
poetry check
```

### 使用 Poetry 发布

```bash
# 构建分发包
poetry build

# 配置 PyPI 令牌
poetry config pypi-token.pypi pypi-AgEIcHlwaS...

# 发布
poetry publish

# 一步构建和发布
poetry publish --build
```

### Poetry 配置

```bash
# 在项目目录中创建虚拟环境（.venv）
poetry config virtualenvs.in-project true

# 使用特定 Python 版本
poetry env use python3.12

# 显示环境信息
poetry env info
```

## pdm 工作流

pdm 是支持 PEP 621 原生的现代 Python 包管理器，并开创了 PEP 582（本地包目录，现已撤回）。

### 基本工作流

```bash
# 安装 pdm
pip install pdm
# 或
pipx install pdm

# 创建新项目
pdm init

# 添加依赖
pdm add httpx pydantic

# 添加开发依赖
pdm add -dG dev pytest mypy ruff

# 从锁文件安装
pdm install

# 更新依赖
pdm update

# 运行命令
pdm run python script.py
pdm run pytest

# 构建
pdm build

# 发布
pdm publish
```

### pdm.lock

pdm 生成跨平台锁文件（`pdm.lock`）。提交到版本控制。

```bash
# 锁定依赖
pdm lock

# 导出到 requirements.txt
pdm export -f requirements -o requirements.txt
```

## conda 用于科学计算

conda 管理包、依赖和环境，支持非 Python 库（C、Fortran、CUDA）。

### 基本工作流

```bash
# 创建环境
conda create -n myproject python=3.12

# 激活
conda activate myproject

# 安装包
conda install numpy pandas scikit-learn

# 从 conda-forge 安装（社区渠道，包更多）
conda install -c conda-forge polars

# 导出环境
conda env export > environment.yml

# 从文件重新创建环境
conda env create -f environment.yml

# 列出环境
conda env list

# 删除环境
conda env remove -n myproject
```

### environment.yml

```yaml
name: myproject
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - numpy>=1.26
  - pandas>=2.2
  - scikit-learn>=1.5
  - matplotlib>=3.9
  - pip:
    - httpx>=0.27       # conda 中不可用时的 pip 包
    - pydantic>=2.0
```

### conda 与 pip

| 方面 | conda | pip |
|--------|-------|-----|
| **包类型** | 任何（C、Fortran、Python、R、CUDA） | 仅 Python |
| **依赖解析** | 包括系统库 | 仅 Python 包 |
| **速度** | 慢 | 快（特别是 uv） |
| **渠道** | conda-forge、defaults、自定义 | PyPI、自定义索引 |
| **最适合** | 科学计算、ML、数据科学 | 通用 Python 开发 |

**建议**：需要非 Python 依赖（CUDA、MKL、系统库）时使用 conda。其他情况优先使用 uv 或 pip。

## pipx 用于 CLI 工具隔离

pipx 在隔离环境中安装 Python CLI 工具，因此它们不会与项目依赖冲突。

```bash
# 安装 pipx
pip install pipx
pipx ensurepath

# 安装 CLI 工具
pipx install ruff
pipx install httpie
pipx install cookiecutter
pipx install pre-commit

# 不安装运行
pipx run cowsay "Hello!"

# 升级
pipx upgrade ruff
pipx upgrade-all

# 列出已安装的工具
pipx list

# 卸载
pipx uninstall ruff
```

**注意**：uv 可以用 `uv tool install` 和 `uvx` 替换 pipx（见上面的 uv 部分）。

## 虚拟环境策略

### 标准库 venv

```bash
# 创建
python -m venv .venv

# 激活
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 停用
deactivate

# 创建访问系统包
python -m venv --system-site-packages .venv
```

### uv venv（推荐）

```bash
# 创建（比 venv 快得多）
uv venv

# 使用特定 Python 创建
uv venv --python 3.12

# 在自定义位置创建
uv venv myenv
```

### virtualenv（第三方）

```bash
pip install virtualenv

# 创建（比 venv 快，功能更多）
virtualenv .venv

# 使用特定 Python 创建
virtualenv -p python3.12 .venv
```

### 约定

- 名称：`.venv`（隐藏目录，被工具和 IDE 广泛识别）
- 位置：项目根目录
- Git：将 `.venv/` 添加到 `.gitignore`
- CI：每次运行时从锁文件重新创建，不要缓存整个 venv

## 依赖解析和锁文件

### 为什么锁文件重要

锁文件固定每个依赖（直接和传递）的确切版本，以确保可重现安装：

- **无锁文件**：`pip install httpx` 可能在不同机器或不同时间安装不同的传递依赖版本。
- **有锁文件**：每次安装产生相同的环境。

### 锁文件格式

| 工具 | 锁文件 | 跨平台 | 格式 |
|------|----------|---------------|--------|
| **uv** | `uv.lock` | 是 | TOML |
| **poetry** | `poetry.lock` | 是 | TOML |
| **pdm** | `pdm.lock` | 是 | TOML |
| **pip-tools** | `requirements.txt` | 否（每平台） | 文本 |
| **conda-lock** | `conda-lock.yml` | 是 | YAML |

### pip-tools 工作流

pip-tools 将 `*.in` 文件编译为固定 `requirements.txt`：

```bash
pip install pip-tools

# 定义抽象依赖
# requirements.in
# httpx>=0.27
# pydantic>=2.0

# 编译为固定版本
pip-compile requirements.in

# 输出：requirements.txt 具有确切版本和哈希
# httpx==0.27.2
# pydantic==2.9.2
# ... 所有传递依赖固定

# 同步环境以匹配
pip-sync requirements.txt

# 升级所有
pip-compile --upgrade requirements.in

# 升级特定包
pip-compile --upgrade-package httpx requirements.in
```

## 私有包索引

### 配置 pip

```bash
# 从私有索引安装
pip install my-internal-package --index-url https://private.pypi.example.com/simple/

# 与 PyPI 一起使用额外索引
pip install my-internal-package --extra-index-url https://private.pypi.example.com/simple/
```

### pip.conf / pip.ini

```ini
[global]
index-url = https://private.pypi.example.com/simple/
extra-index-url = https://pypi.org/simple/
trusted-host = private.pypi.example.com
```

### 使用 keyring 进行身份验证

```bash
pip install keyring keyrings.google-artifactregistry-auth

# keyring 自动为配置的索引提供凭据
pip install my-package --index-url https://us-central1-python.pkg.dev/my-project/my-repo/simple/
```

### pyproject.toml 配置

**uv**：
```toml
[[tool.uv.index]]
name = "internal"
url = "https://private.pypi.example.com/simple/"

[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple/"
```

**poetry**：
```toml
[[tool.poetry.source]]
name = "internal"
url = "https://private.pypi.example.com/simple/"
priority = "primary"
```

### devpi（私有 PyPI 服务器）

```bash
# 安装 devpi
pip install devpi-server devpi-client

# 初始化和启动
devpi-server --init
devpi-server --start

# 配置客户端
devpi use http://localhost:3141
devpi login root --password=""
devpi index -c root/internal
devpi use root/internal

# 上传包
devpi upload
```

## 最佳实践

1. **始终使用虚拟环境**。永远不要将项目依赖安装到系统 Python 中。在 pip 配置中设置 `require-virtualenv = true`。

2. **提交您的锁文件**。无论是 `uv.lock`、`poetry.lock`、`pdm.lock` 还是编译的 `requirements.txt`，提交到版本控制以实现可重现构建。

3. **分离依赖组**。使用可选依赖组（`[project.optional-dependencies]`）或工具特定组以保持生产依赖精简：
   ```toml
   [project.optional-dependencies]
   dev = ["pytest", "mypy", "ruff"]
   docs = ["sphinx"]
   ```

4. **库使用 `>=` 最低版本**，应用使用精确固定：
   - 库：`dependencies = ["httpx>=0.27"]`
   - 应用：使用锁文件固定确切版本

5. **优先使用 uv 以提高速度**。uv 的解析和安装速度比 pip 快 10-100 倍。它是即插即用替代品。

6. **使用 pipx 或 `uv tool` 进行全局 CLI 工具**。如果 ruff、black、httpie 等仅作为独立工具需要，请不要将它们安装到您的项目虚拟环境中。

7. **定期更新依赖**：
   ```bash
   # uv
   uv lock --upgrade

   # poetry
   poetry update

   # pip-tools
   pip-compile --upgrade requirements.in
   ```

8. **审计漏洞**：
   ```bash
   pip install pip-audit
   pip-audit

   # 或使用 uv
   uv pip audit
   ```

9. **高安全环境使用哈希检查**：
   ```bash
   # pip-tools 生成哈希
   pip-compile --generate-hashes requirements.in

   # pip 验证
   pip install --require-hashes -r requirements.txt
   ```

10. **使用 `.python-version` 或 `pyproject.toml` 中的 `requires-python` 固定 Python 版本** 以防止环境漂移。
