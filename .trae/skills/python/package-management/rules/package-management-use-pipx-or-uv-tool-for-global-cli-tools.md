---
title: "使用 pipx 或 `uv tool` 安装全局 CLI 工具"
impact: CRITICAL
impactDescription: "对于正确性或安全性至关重要"
tags: python, pip, uv, poetry, pdm, conda, pipx, virtualenv, dependencies, package-management, installing-packages, managing-dependencies, choosing-between-pipuvpoetrypdmconda
---

## 使用 pipx 或 `uv tool` 安装全局 CLI 工具

如果 ruff、black、httpie 等工具仅作为独立工具使用，请不要将它们安装到您的项目虚拟环境中。