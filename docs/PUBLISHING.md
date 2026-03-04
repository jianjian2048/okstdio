# 发布到 PyPI 指南

本文档说明如何将 okstdio 发布到 PyPI。

## 前置要求

1. **注册 PyPI 账号**
   - 生产环境：https://pypi.org/account/register/
   - 测试环境：https://test.pypi.org/account/register/

2. **安装构建工具**
   ```bash
   pip install build twine
   ```
   
   或使用 uv（推荐）：
   ```bash
   uv tool install build
   uv tool install twine
   ```

## 发布步骤

### 方法一：使用 uv（推荐）

uv 提供了简化的发布流程：

```bash
# 1. 构建包
uv build

# 2. 发布到 PyPI（会提示输入用户名和密码）
uv publish

# 或先发布到 Test PyPI 测试
uv publish --publish-url https://test.pypi.org/legacy/
```

### 方法二：使用传统工具

#### 1. 清理旧的构建文件

```bash
# Windows PowerShell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Linux/Mac
rm -rf dist/ build/ *.egg-info
```

#### 2. 构建分发包

```bash
python -m build
```

这会在 `dist/` 目录生成两个文件：
- `okstdio-0.1.0.tar.gz` (源码分发)
- `okstdio-0.1.0-py3-none-any.whl` (wheel 分发)

#### 3. 检查构建的包

```bash
twine check dist/*
```

确保没有错误或警告。

#### 4. 测试发布（可选但推荐）

先发布到 Test PyPI 测试：

```bash
twine upload --repository testpypi dist/*
```

测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ okstdio
```

#### 5. 正式发布到 PyPI

```bash
twine upload dist/*
```

会提示输入：
- Username: 你的 PyPI 用户名
- Password: 你的 PyPI 密码（或 API Token）

## 使用 API Token（推荐）

为了安全，建议使用 API Token 而不是密码：

### 1. 生成 API Token

访问 https://pypi.org/manage/account/token/ 创建 token

### 2. 配置 .pypirc

创建 `~/.pypirc` 文件（Windows: `%USERPROFILE%\.pypirc`）：

```ini
[pypi]
username = __token__
password = pypi-AgEIcH...你的token...

[testpypi]
username = __token__
password = pypi-AgEIcH...你的token...
```

**注意**：不要将 `.pypirc` 提交到 git！

### 3. 使用配置文件发布

```bash
twine upload dist/*
```

现在不需要手动输入用户名和密码了。

## 版本管理

### 更新版本号

编辑 `pyproject.toml`：

```toml
[project]
version = "0.1.1"  # 更新版本号
```

版本号遵循语义化版本规范：
- **MAJOR.MINOR.PATCH** (例如: 1.2.3)
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修复

### 发布新版本

```bash
# 1. 更新版本号（编辑 pyproject.toml）
# 2. 更新 CHANGELOG（如果有）
# 3. 清理旧构建
rm -rf dist/
# 4. 构建新版本
uv build
# 5. 发布
uv publish
```

## 发布检查清单

在发布前确保：

- [ ] 所有测试通过（`pytest tests/`）
- [ ] 更新了版本号
- [ ] 更新了 README.md 和文档
- [ ] 更新了 CHANGELOG（如果有）
- [ ] LICENSE 文件存在且正确
- [ ] 清理了临时文件和缓存
- [ ] `pyproject.toml` 配置正确
- [ ] 构建包通过检查（`twine check`）
- [ ] 在 Test PyPI 测试过（可选）

## 常见问题

### Q: 上传失败：文件已存在

A: PyPI 不允许覆盖已发布的版本。你需要：
1. 更新版本号
2. 重新构建
3. 重新上传

### Q: 如何撤回已发布的版本？

A: PyPI 不允许删除已发布的版本，但可以"yank"它：
```bash
twine upload --repository pypi --skip-existing dist/*
```

访问 PyPI 项目页面手动 yank 版本。

### Q: 构建失败怎么办？

A: 检查：
1. `pyproject.toml` 配置是否正确
2. 所有必需文件是否存在
3. Python 版本是否符合要求
4. 依赖包是否都已安装

### Q: 如何查看包的详细信息？

A: 解压 wheel 文件查看：
```bash
unzip -l dist/okstdio-0.1.0-py3-none-any.whl
```

## 自动化发布（GitHub Actions）

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

需要在 GitHub 仓库设置中添加 `PYPI_API_TOKEN` secret。

## 快速命令参考

```bash
# 使用 uv（推荐）
uv build                                              # 构建包
uv publish                                            # 发布到 PyPI
uv publish --publish-url https://test.pypi.org/legacy/  # 发布到 Test PyPI

# 使用传统工具
python -m build                                       # 构建包
twine check dist/*                                    # 检查包
twine upload --repository testpypi dist/*            # 测试发布
twine upload dist/*                                   # 正式发布
```

## 相关链接

- [PyPI 官网](https://pypi.org/)
- [Test PyPI](https://test.pypi.org/)
- [Python 打包指南](https://packaging.python.org/)
- [语义化版本](https://semver.org/lang/zh-CN/)
- [Twine 文档](https://twine.readthedocs.io/)

---

祝发布顺利！🎉

