---
title: "使用 CliRunner 测试"
impact: MEDIUM
impactDescription: "通用最佳实践"
tags: python, cli, argparse, click, typer, rich, textual, tui, building-cli-tools-with-argparseclicktyper, rich-terminal-output, tui-applications-with-textual
---

## 使用 CliRunner 测试

Click 和 Typer 都提供 `CliRunner` 进行测试，无需启动子进程。