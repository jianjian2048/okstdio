---
title: "始终使用虚拟环境"
impact: CRITICAL
impactDescription: "对于正确性或安全性至关重要"
tags: python, pip, uv, poetry, pdm, conda, pipx, virtualenv, dependencies, package-management, installing-packages, managing-dependencies, choosing-between-pipuvpoetrypdmconda
---

## 始终使用虚拟环境

永远不要将项目依赖安装到系统 Python 中。在 pip 配置中设置 `require-virtualenv = true`。