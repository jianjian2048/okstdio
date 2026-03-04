---
title: "将诊断信息写入 stderr"
impact: MEDIUM
impactDescription: "通用最佳实践"
tags: python, cli, argparse, click, typer, rich, textual, tui, building-cli-tools-with-argparseclicktyper, rich-terminal-output, tui-applications-with-textual
---

## 将诊断信息写入 stderr

使用 `stderr` 进行进度、警告和错误。将 `stdout` 保留用于数据输出：