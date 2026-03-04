---
title: "尊重 `NO_COLOR`"
impact: MEDIUM
impactDescription: "通用最佳实践"
tags: python, cli, argparse, click, typer, rich, textual, tui, building-cli-tools-with-argparseclicktyper, rich-terminal-output, tui-applications-with-textual
---

## 尊重 `NO_COLOR`

检查 `NO_COLOR` 环境变量，并在设置时禁用颜色/格式化。