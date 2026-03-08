# 发布到 PyPI 指南

本项目使用 `uv` 作为包管理器，构建后端为 `uv_build`。

## 前置要求

1. **安装 uv**（如果未安装）
   ```bash
   pip install uv
   # 或 Windows
   winget install astral-sh.uv
   ```

2. **注册 PyPI 账号**
   - 生产环境：https://pypi.org/account/register/
   - 测试环境：https://test.pypi.org/account/register/

3. **生成 API Token**（推荐，比密码更安全）
   - 生产：https://pypi.org/manage/account/token/
   - 测试：https://test.pypi.org/manage/account/token/

4. **配置 Token**（一次性配置，之后无需重复）

   创建或编辑 `~/.pypirc`（Windows：`%USERPROFILE%\.pypirc`）：

   ```ini
   [pypi]
   username = __token__
   password = pypi-AgEIcH...你的正式token...

   [testpypi]
   username = __token__
   password = pypi-AgEIcH...你的测试token...
   ```

   > **注意**：不要将 `.pypirc` 提交到 git！

---

## 发布流程

### 第一步：更新版本号

编辑 `pyproject.toml`，遵循语义化版本规范：

```toml
[project]
version = "1.0.1"  # MAJOR.MINOR.PATCH
```

版本规则：
- **PATCH**（如 1.0.0 → 1.0.1）：Bug 修复
- **MINOR**（如 1.0.0 → 1.1.0）：向后兼容的新功能
- **MAJOR**（如 1.0.0 → 2.0.0）：不兼容的 API 变更

### 第二步：运行测试

```bash
pytest tests/
```

确保所有测试通过后再继续。

### 第三步：构建包

```bash
uv build
```

构建完成后，`dist/` 目录会生成：
- `okstdio-1.0.1.tar.gz`（源码包）
- `okstdio-1.0.1-py3-none-any.whl`（wheel 包）

### 第四步（可选）：先发布到 Test PyPI 验证

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

验证安装：
```bash
pip install --index-url https://test.pypi.org/simple/ okstdio
pip install --index-url https://test.pypi.org/simple/ "okstdio[tui]"
```

### 第五步：发布到正式 PyPI

```bash
uv publish
```

发布后用户即可通过以下方式安装：

```bash
uv add okstdio
uv add "okstdio[tui]"

# 或 pip
pip install okstdio
pip install "okstdio[tui]"
```

---

## 快速参考

```bash
# 完整发布流程
pytest tests/                                              # 1. 跑测试
# 编辑 pyproject.toml 更新版本号                           # 2. 改版本
uv build                                                   # 3. 构建
uv publish --publish-url https://test.pypi.org/legacy/    # 4. 测试发布（可选）
uv publish                                                 # 5. 正式发布
```

---

## 发布检查清单

- [ ] 所有测试通过（`pytest tests/`）
- [ ] `pyproject.toml` 版本号已更新
- [ ] README.md 文档已更新
- [ ] 清理了临时文件（`dist/` 旧版本）
- [ ] Test PyPI 测试过（可选）

---

## 常见问题

**Q：上传失败"File already exists"**

PyPI 不允许覆盖已发布的版本。需要更新版本号重新构建发布。

**Q：uv publish 提示认证失败**

检查 `~/.pypirc` 配置，确认 token 填写正确，用户名固定为 `__token__`。

**Q：如何撤回已发布的版本？**

PyPI 不支持删除，但可以在项目页面 "yank"（标记为不推荐），用户安装时会收到警告。

---

## 相关链接

- [PyPI 官网](https://pypi.org/)
- [Test PyPI](https://test.pypi.org/)
- [uv 文档](https://docs.astral.sh/uv/)
- [语义化版本规范](https://semver.org/lang/zh-CN/)
