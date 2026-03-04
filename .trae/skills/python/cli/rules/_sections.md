# Python CLI 开发规则

Python CLI 开发的最佳实践和规则。

## 规则

| # | 规则 | 影响 | 文件 |
|---|------|--------|------|
| 1 | 为所有内容编写 `--help` | MEDIUM | [`cli-write-help-for-everything.md`](cli-write-help-for-everything.md) |
| 2 | 支持 `--json` 输出 | MEDIUM | [`cli-support-json-output.md`](cli-support-json-output.md) |
| 3 | 将诊断信息写入 stderr | MEDIUM | [`cli-write-to-stderr-for-diagnostics.md`](cli-write-to-stderr-for-diagnostics.md) |
| 4 | 一致地使用退出码 | MEDIUM | [`cli-use-exit-codes-consistently.md`](cli-use-exit-codes-consistently.md) |
| 5 | 尊重 `NO_COLOR` | MEDIUM | [`cli-respect-no-color.md`](cli-respect-no-color.md) |
| 6 | 使用 CliRunner 测试 | MEDIUM | [`cli-test-with-clirunner.md`](cli-test-with-clirunner.md) |
| 7 | 添加 shell 自动完成 | MEDIUM | [`cli-add-shell-completion.md`](cli-add-shell-completion.md) |
| 8 | 在 Typer 中使用 `Annotated` 参数 | MEDIUM | [`cli-use-annotated-parameters-in-typer.md`](cli-use-annotated-parameters-in-typer.md) |
| 9 | 提供 `--verbose` 和 `--quiet` 标志 | LOW | [`cli-provide-verbose-and-quiet-flags.md`](cli-provide-verbose-and-quiet-flags.md) |
| 10 | 版本标志 | CRITICAL | [`cli-version-flag.md`](cli-version-flag.md) |