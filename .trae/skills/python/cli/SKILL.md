---
name: cli
description: |
  Python 中构建命令行界面和终端应用程序的指南。
  用于：使用 argparse/click/typer 构建 CLI 工具、丰富的终端输出、使用 textual 构建 TUI 应用程序、CLI 测试策略、输出格式化、退出码
  不用于：Python 项目设置或打包（使用 project-system）、安装 CLI 工具（使用 package-management）
license: MIT
metadata:
  displayName: "Python CLI 开发"
  author: "Tyler-R-Kendrick"
  version: "1.0.0"
  tags:
    - python
    - cli
    - argparse
    - click
    - typer
    - rich
    - textual
    - tui
compatibility: claude, copilot, cursor
references:
  - title: "Typer 文档"
    url: "https://typer.tiangolo.com/"
  - title: "Click 文档"
    url: "https://click.palletsprojects.com/"
  - title: "Rich 文档"
    url: "https://rich.readthedocs.io/"
  - title: "Python argparse 文档"
    url: "https://docs.python.org/3/library/argparse.html"
---

# Python CLI 开发

## 概述

Python 是构建命令行工具最流行的语言之一，从简单脚本到复杂的多命令应用程序。生态系统范围从标准库的 `argparse` 到像 `typer` 这样的高级框架（从类型提示生成 CLI），以及像 `rich` 和 `textual` 这样的丰富输出库，用于构建美观的终端界面。

## 工具比较

| 功能 | argparse | click | typer | fire | cement |
|---------|----------|-------|-------|------|--------|
| **标准库** | 是 | 否 | 否 | 否 | 否 |
| **方法** | 命令式 | 装饰器基础 | 类型提示基础 | 检查 | 全面框架 |
| **子命令** | 是（子解析器） | 是（组） | 是（应用 + 命令） | 自动 | 是 |
| **自动完成** | 否（附加组件） | 是（插件） | 是（内置） | 否 | 是 |
| **测试** | 手动 | `CliRunner` | `CliRunner`（通过 click） | 手动 | 内置 |
| **丰富输出** | 手动 | 插件生态系统 | 内置（通过 rich） | 否 | 是 |
| **学习曲线** | 低 | 中等 | 低 | 非常低 | 高 |
| **依赖** | 无 | click | typer, click, rich | fire | cement |
| **最适合** | 简单工具，无依赖脚本 | 中等至大型 CLI | 具有类型安全的现代 CLI | 快速原型 | 企业 CLI |

**建议**：对新 CLI 项目使用 **typer** -- 它提供了最佳的开发人员体验，具有类型提示、自动完成和丰富的集成。当您不能添加依赖时使用 **argparse**。当您需要最大灵活性和大型插件生态系统时使用 **click**。

## argparse 模式

argparse 是 Python 内置的参数解析库。它不需要外部依赖。

### 基本用法

```python
import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mytool",
        description="一个执行有用操作的工具",
        epilog="示例：mytool process --input data.csv --format json",
    )
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", default="-", help="输出文件（默认：stdout）")
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细输出")
    parser.add_argument("--count", type=int, default=1, help="重复次数")

    args = parser.parse_args()

    if args.verbose:
        print(f"正在处理 {args.input}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 子命令

```python
import argparse


def cmd_init(args: argparse.Namespace) -> int:
    print(f"正在初始化项目：{args.name}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    print(f"正在使用配置构建：{args.config}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="mytool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化新项目")
    init_parser.add_argument("name", help="项目名称")
    init_parser.set_defaults(func=cmd_init)

    # build 子命令
    build_parser = subparsers.add_parser("build", help="构建项目")
    build_parser.add_argument("-c", "--config", default="release", help="构建配置")
    build_parser.set_defaults(func=cmd_build)

    args = parser.parse_args()
    return args.func(args)
```

### 互斥组

```python
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--json", action="store_true", help="以 JSON 格式输出")
group.add_argument("--csv", action="store_true", help="以 CSV 格式输出")
group.add_argument("--table", action="store_true", help="以表格格式输出")
```

### 自定义类型

```python
import argparse
from pathlib import Path


def existing_path(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"路径不存在：{value}")
    return path


def port_number(value: str) -> int:
    port = int(value)
    if not (1 <= port <= 65535):
        raise argparse.ArgumentTypeError(f"无效端口：{value}（必须是 1-65535）")
    return port


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=existing_path, help="配置文件路径")
parser.add_argument("--port", type=port_number, default=8080, help="服务器端口")
```

## Click 深入解析

Click 是一个成熟的、基于装饰器的 CLI 构建框架。它强调可组合性和可测试性。

### 安装

```bash
pip install click
```

### 基本命令

```python
import click


@click.command()
@click.argument("name")
@click.option("--greeting", "-g", default="Hello", help="要使用的问候语")
@click.option("--count", "-c", default=1, type=int, help="问候次数")
@click.option("--verbose", "-v", is_flag=True, help="启用详细输出")
def greet(name: str, greeting: str, count: int, verbose: bool) -> None:
    """用 NAME 次数问候某人。"""
    if verbose:
        click.echo(f"正在问候 {name} {count} 次...")
    for _ in range(count):
        click.echo(f"{greeting}, {name}!")


if __name__ == "__main__":
    greet()
```

### 命令组（子命令）

```python
import click


@click.group()
@click.option("--debug/--no-debug", default=False, help="启用调试模式")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """我的多命令 CLI 工具。"""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@cli.command()
@click.argument("name")
@click.pass_context
def init(ctx: click.Context, name: str) -> None:
    """初始化新项目。"""
    if ctx.obj["debug"]:
        click.echo("调试模式已开启")
    click.echo(f"正在初始化 {name}...")


@cli.command()
@click.option("--config", "-c", default="release", help="构建配置")
@click.pass_context
def build(ctx: click.Context, config: str) -> None:
    """构建项目。"""
    click.echo(f"正在使用配置构建：{config}")


if __name__ == "__main__":
    cli()
```

### 上下文和状态传递

```python
import click


class AppConfig:
    def __init__(self, debug: bool = False, output_format: str = "text"):
        self.debug = debug
        self.output_format = output_format


pass_config = click.make_pass_decorator(AppConfig, ensure=True)


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.option("--format", "output_format", type=click.Choice(["text", "json", "csv"]))
@click.pass_context
def cli(ctx: click.Context, debug: bool, output_format: str) -> None:
    ctx.obj = AppConfig(debug=debug, output_format=output_format or "text")


@cli.command()
@pass_config
def status(config: AppConfig) -> None:
    """显示状态。"""
    if config.output_format == "json":
        click.echo('{"status": "ok"}')
    else:
        click.echo("状态：OK")
```

### 文件处理

```python
import click


@click.command()
@click.argument("input_file", type=click.File("r"))
@click.argument("output_file", type=click.File("w"), default="-")  # 默认为 stdout
def process(input_file, output_file) -> None:
    """处理 INPUT_FILE 并写入 OUTPUT_FILE。"""
    for line in input_file:
        output_file.write(line.upper())


@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, resolve_path=True))
def scan(directory: str) -> None:
    """扫描 DIRECTORY 中的文件。"""
    click.echo(f"正在扫描：{directory}")
```

### 使用 CliRunner 测试

```python
from click.testing import CliRunner
from myapp.cli import cli


def test_init_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "myproject"])
    assert result.exit_code == 0
    assert "正在初始化 myproject" in result.output


def test_build_with_debug():
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "build", "--config", "debug"])
    assert result.exit_code == 0


def test_file_processing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("input.txt", "w") as f:
            f.write("hello\nworld\n")
        result = runner.invoke(process, ["input.txt", "output.txt"])
        assert result.exit_code == 0
        with open("output.txt") as f:
            assert f.read() == "HELLO\nWORLD\n"
```

### 有用的 Click 装饰器和功能

```python
import click

# 密码提示（隐藏输入）
@click.command()
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def set_password(password: str) -> None:
    click.echo("密码已设置。")

# 选择类型
@click.command()
@click.option("--color", type=click.Choice(["red", "green", "blue"], case_sensitive=False))
def paint(color: str) -> None:
    click.echo(f"正在绘制 {color}")

# 范围类型
@click.command()
@click.option("--count", type=click.IntRange(1, 100), default=10)
def repeat(count: int) -> None:
    click.echo(f"重复 {count} 次")

# 进度条
@click.command()
def download() -> None:
    items = range(1000)
    with click.progressbar(items, label="正在下载") as bar:
        for item in bar:
            pass  # 执行工作

# 确认
@click.command()
@click.confirmation_option(prompt="您确定要删除所有内容吗？")
def delete_all() -> None:
    click.echo("已删除所有内容。")
```

## Typer 深入解析

Typer 基于 click 构建，但使用 Python 类型提示来定义 CLI 接口。它生成美观的帮助文本，并开箱即用地与 rich 集成。

### 安装

```bash
pip install typer

# 带有所有可选依赖项（rich、shellingham）
pip install "typer[all]"
```

### 基本命令

```python
import typer


def main(
    name: str,
    greeting: str = "Hello",
    count: int = 1,
    verbose: bool = False,
) -> None:
    """按 NAME 问候某人。"""
    if verbose:
        typer.echo(f"正在问候 {name} {count} 次...")
    for _ in range(count):
        typer.echo(f"{greeting}, {name}!")


if __name__ == "__main__":
    typer.run(main)
```

### 多命令应用程序

```python
import typer
from typing import Annotated, Optional
from enum import Enum
from pathlib import Path

app = typer.Typer(help="我很棒的 CLI 工具。")


class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    csv = "csv"


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="项目名称")],
    template: Annotated[str, typer.Option("--template", "-t", help="要使用的模板")] = "default",
    force: Annotated[bool, typer.Option("--force", "-f", help="覆盖现有")] = False,
) -> None:
    """初始化新项目。"""
    if force:
        typer.echo(f"强制创建 {name}，使用模板 {template}")
    else:
        typer.echo(f"正在创建 {name}，使用模板 {template}")


@app.command()
def build(
    config: Annotated[str, typer.Option(help="构建配置")] = "release",
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="输出目录")] = Path("dist"),
    format: Annotated[OutputFormat, typer.Option(help="输出格式")] = OutputFormat.text,
) -> None:
    """构建项目。"""
    typer.echo(f"正在构建 [{config}] -> {output_dir}（格式：{format.value}）")


@app.command()
def clean(
    all: Annotated[bool, typer.Option("--all", help="删除所有工件")] = False,
) -> None:
    """清理构建工件。"""
    if all:
        confirmed = typer.confirm("删除所有工件，包括缓存吗？")
        if not confirmed:
            raise typer.Abort()
    typer.echo("已清理。")


if __name__ == "__main__":
    app()
```

### Annotated 参数（推荐模式）

```python
from typing import Annotated
import typer

app = typer.Typer()


@app.command()
def deploy(
    # 必需参数
    environment: Annotated[str, typer.Argument(help="目标环境")],
    # 带短标志的可选参数
    tag: Annotated[str, typer.Option("--tag", "-t", help="镜像标签")] = "latest",
    # 布尔标志
    dry_run: Annotated[bool, typer.Option("--dry-run", help="预览但不部署")] = False,
    # 提示输入
    token: Annotated[str, typer.Option(prompt=True, hide_input=True, help="认证令牌")] = ...,
    # 枚举选择
    region: Annotated[
        str,
        typer.Option(help="云区域", click_type=typer.Choice(["us-east-1", "eu-west-1", "ap-south-1"]))
    ] = "us-east-1",
) -> None:
    """将应用程序部署到目标环境。"""
    if dry_run:
        typer.echo(f"[预览] 将部署 {tag} 到 {environment} 的 {region}")
    else:
        typer.echo(f"正在部署 {tag} 到 {environment} 的 {region}...")
```

### 自动完成

```bash
# 生成完成脚本
my-cli --install-completion bash
my-cli --install-completion zsh
my-cli --install-completion fish

# 显示完成脚本而不安装
my-cli --show-completion bash
```

### Typer 测试

Typer 在底层使用 Click 的 `CliRunner`：

```python
from typer.testing import CliRunner
from myapp.cli import app

runner = CliRunner()


def test_init():
    result = runner.invoke(app, ["init", "myproject"])
    assert result.exit_code == 0
    assert "正在创建 myproject" in result.output


def test_init_with_force():
    result = runner.invoke(app, ["init", "myproject", "--force"])
    assert result.exit_code == 0
    assert "强制创建" in result.output


def test_build_json_format():
    result = runner.invoke(app, ["build", "--format", "json"])
    assert result.exit_code == 0
    assert "json" in result.output


def test_clean_aborted():
    result = runner.invoke(app, ["clean", "--all"], input="n\n")
    assert result.exit_code == 1  # 已中止
```

### 嵌套命令组（子应用程序）

```python
import typer

app = typer.Typer()
users_app = typer.Typer(help="用户管理命令。")
app.add_typer(users_app, name="users")


@users_app.command("list")
def list_users() -> None:
    """列出所有用户。"""
    typer.echo("user1\nuser2\nuser3")


@users_app.command("create")
def create_user(name: str, email: str) -> None:
    """创建新用户。"""
    typer.echo(f"已创建用户 {name} ({email})")


# 用法：mycli users list
#        mycli users create "Jane" "jane@example.com"
```

## Rich 库

Rich 是一个用于美观终端输出的库：颜色、表格、进度条、语法高亮、Markdown 渲染等。

### 安装

```bash
pip install rich
```

### 控制台标记

```python
from rich.console import Console

console = Console()

# 样式化文本
console.print("[bold red]错误：[/bold red] 出现问题")
console.print("[green]成功！[/green] 操作已完成。")
console.print("[dim italic]这是暗淡和斜体的[/dim italic]")

# Emoji
console.print(":rocket: 正在发射...")

# 链接
console.print("访问 [link=https://example.com]我们的网站[/link]")

# 打印时高亮（自动检测并高亮数字、字符串等）
console.print({"name": "Alice", "age": 30, "active": True})
```

### 表格

```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="部署状态")
table.add_column("服务", style="cyan", no_wrap=True)
table.add_column("版本", style="magenta")
table.add_column("状态", justify="center")
table.add_column("运行时间", justify="right", style="green")

table.add_row("api-gateway", "2.3.1", "[green]健康[/green]", "14天3小时")
table.add_row("auth-service", "1.8.0", "[green]健康[/green]", "14天3小时")
table.add_row("worker", "3.0.2", "[red]降级[/red]", "2小时15分钟")
table.add_row("database", "16.1", "[green]健康[/green]", "30天12小时")

console.print(table)
```

### 进度条

```python
import time
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# 简单进度条
from rich.progress import track

for item in track(range(100), description="正在处理..."):
    time.sleep(0.02)

# 高级多任务进度
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
) as progress:
    download_task = progress.add_task("正在下载...", total=1000)
    install_task = progress.add_task("正在安装...", total=500)

    while not progress.finished:
        progress.update(download_task, advance=5)
        progress.update(install_task, advance=2)
        time.sleep(0.01)
```

### 面板、树和列

```python
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns

console = Console()

# 面板
console.print(Panel("这是重要信息", title="通知", border_style="yellow"))

# 树
tree = Tree("[bold]项目结构[/bold]")
src = tree.add("[folder]src/")
src.add("[file]main.py")
src.add("[file]config.py")
utils = src.add("[folder]utils/")
utils.add("[file]helpers.py")
tests = tree.add("[folder]tests/")
tests.add("[file]test_main.py")
console.print(tree)

# 列
data = [Panel(f"项目 {i}", expand=True) for i in range(12)]
console.print(Columns(data))
```

### 实时显示

```python
import time
from rich.live import Live
from rich.table import Table


def generate_table(step: int) -> Table:
    table = Table()
    table.add_column("步骤")
    table.add_column("状态")
    for i in range(step + 1):
        table.add_row(f"步骤 {i}", "[green]已完成[/green]")
    if step < 5:
        table.add_row(f"步骤 {step + 1}", "[yellow]运行中...[/yellow]")
    return table


with Live(generate_table(0), refresh_per_second=4) as live:
    for step in range(6):
        time.sleep(0.5)
        live.update(generate_table(step))
```

### 语法高亮和日志记录

```python
from rich.console import Console
from rich.syntax import Syntax
import logging
from rich.logging import RichHandler

console = Console()

# 语法高亮
code = '''
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)

# Rich 日志处理程序
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("myapp")
log.info("应用程序已启动")
log.warning("磁盘空间不足")
log.error("连接失败")
```

## Textual 用于 TUI 应用程序

Textual 是一个用于构建终端用户界面（TUI）的框架，具有类似 CSS 的样式系统和响应式小部件模型。

### 安装

```bash
pip install textual

# 带有开发工具（用于实时 CSS 编辑）
pip install "textual[dev]"
```

### 基本应用程序

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Input, DataTable


class MyApp(App):
    """一个简单的 Textual 应用程序。"""

    CSS = """
    Screen {
        layout: vertical;
    }
    #sidebar {
        width: 30;
        background: $surface;
        padding: 1;
    }
    #main {
        width: 1fr;
        padding: 1;
    }
    Button {
        margin: 1 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
        ("d", "toggle_dark", "切换深色模式"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("导航", classes="title")
                yield Button("仪表板", id="btn-dashboard", variant="primary")
                yield Button("设置", id="btn-settings")
                yield Button("日志", id="btn-logs")
            with Vertical(id="main"):
                yield Static("欢迎使用 MyApp", id="content")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        content = self.query_one("#content", Static)
        content.update(f"您点击了：{event.button.id}")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    MyApp().run()
```

### 小部件

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, ListView, ListItem, Label, RichLog


class DataApp(App):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="搜索...", id="search")
        yield DataTable()
        yield RichLog(id="log")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("姓名", "角色", "状态")
        table.add_rows([
            ("Alice", "工程师", "活跃"),
            ("Bob", "设计师", "离开"),
            ("Carol", "经理", "活跃"),
        ])

    def on_input_changed(self, event: Input.Changed) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"搜索：{event.value}")
```

### 响应式属性

```python
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Static


class Counter(Static):
    count: reactive[int] = reactive(0)

    def render(self) -> str:
        return f"计数：{self.count}"

    def watch_count(self, new_value: int) -> None:
        if new_value > 10:
            self.styles.color = "red"

    def on_click(self) -> None:
        self.count += 1
```

### CSS 样式

Textual 使用类似 CSS 的语言进行样式设置。样式可以定义在内联、`CSS` 类变量中，或外部 `.tcss` 文件中。

```python
class MyApp(App):
    CSS_PATH = "styles.tcss"  # 从外部文件加载
```

```css
/* styles.tcss */
Screen {
    layout: horizontal;
}

#sidebar {
    width: 25%;
    background: $surface;
    border-right: solid $primary;
    padding: 1 2;
}

#main {
    width: 75%;
    padding: 1 2;
}

Button {
    width: 100%;
    margin: 1 0;
}

Button:hover {
    background: $primary-lighten-2;
}

DataTable > .datatable--header {
    background: $primary;
    color: $text;
}
```

## 输出格式化

### JSON 输出模式

提供 `--json` 标志以实现机器可读输出：

```python
import json
import typer
from typing import Annotated

app = typer.Typer()


@app.command()
def status(
    json_output: Annotated[bool, typer.Option("--json", help="以 JSON 格式输出")] = False,
) -> None:
    """显示系统状态。"""
    data = {
        "status": "healthy",
        "services": [
            {"name": "api", "status": "up", "latency_ms": 42},
            {"name": "db", "status": "up", "latency_ms": 5},
        ],
        "version": "1.2.0",
    }

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        console.print(f"[bold]状态：[/bold] {data['status']}")
        table = Table()
        table.add_column("服务")
        table.add_column("状态")
        table.add_column("延迟")
        for svc in data["services"]:
            table.add_row(svc["name"], svc["status"], f"{svc['latency_ms']}ms")
        console.print(table)
```

### 颜色/无颜色支持

尊重 `NO_COLOR` 环境变量（参见 https://no-color.org）：

```python
import os
from rich.console import Console

# Rich 自动尊重 NO_COLOR
console = Console(no_color=os.environ.get("NO_COLOR") is not None)

# 或通过 CLI 标志强制无颜色
import typer

app = typer.Typer()

@app.callback()
def main(no_color: bool = False) -> None:
    if no_color:
        os.environ["NO_COLOR"] = "1"
```

### 使用 tabulate 进行表格格式化

```python
from tabulate import tabulate

data = [
    ["api-gateway", "2.3.1", "健康"],
    ["auth-service", "1.8.0", "健康"],
    ["worker", "3.0.2", "降级"],
]
headers = ["服务", "版本", "状态"]

# 多种输出格式
print(tabulate(data, headers=headers, tablefmt="grid"))
print(tabulate(data, headers=headers, tablefmt="github"))
print(tabulate(data, headers=headers, tablefmt="plain"))
```

## 退出码和错误处理

### 标准退出码

```python
import sys

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2        # 无效参数
EXIT_NOT_FOUND = 3          # 资源未找到
EXIT_PERMISSION_DENIED = 4  # 权限不足


def main() -> int:
    try:
        result = do_work()
        return EXIT_SUCCESS
    except FileNotFoundError as e:
        print(f"错误：{e}", file=sys.stderr)
        return EXIT_NOT_FOUND
    except PermissionError as e:
        print(f"错误：{e}", file=sys.stderr)
        return EXIT_PERMISSION_DENIED
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return EXIT_GENERAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
```

### Typer 中的错误处理

```python
import typer
from rich.console import Console

app = typer.Typer()
err_console = Console(stderr=True)


@app.command()
def deploy(environment: str) -> None:
    """部署到环境。"""
    valid_envs = {"dev", "staging", "production"}
    if environment not in valid_envs:
        err_console.print(f"[red]错误：[/red] 未知环境 '{environment}'")
        err_console.print(f"有效环境：{', '.join(sorted(valid_envs))}")
        raise typer.Exit(code=2)

    if environment == "production":
        confirmed = typer.confirm("部署到生产环境吗？", abort=True)

    typer.echo(f"正在部署到 {environment}...")
```

### Click 中的错误处理

```python
import click
import sys


class AppError(click.ClickException):
    """带有彩色输出的自定义错误。"""

    def format_message(self) -> str:
        return f"错误：{self.message}"


@click.command()
@click.argument("config_path", type=click.Path(exists=True))
def run(config_path: str) -> None:
    try:
        load_config(config_path)
    except ValueError as e:
        raise AppError(str(e))
    except Exception as e:
        click.echo(f"致命错误：{e}", err=True)
        sys.exit(1)
```

## CLI 测试策略

### 使用 pytest 和 CliRunner 测试

```python
import pytest
from typer.testing import CliRunner
from myapp.cli import app

runner = CliRunner()


class TestInitCommand:
    def test_basic_init(self):
        result = runner.invoke(app, ["init", "myproject"])
        assert result.exit_code == 0
        assert "myproject" in result.output

    def test_init_with_template(self):
        result = runner.invoke(app, ["init", "myproject", "--template", "fastapi"])
        assert result.exit_code == 0
        assert "fastapi" in result.output

    def test_init_invalid_name(self):
        result = runner.invoke(app, ["init", ""])
        assert result.exit_code != 0

    def test_help_text(self):
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "初始化" in result.output


class TestOutputFormats:
    def test_json_output(self):
        result = runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert "status" in data

    def test_text_output(self):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "状态：" in result.output
```

### 使用文件系统隔离测试

```python
from click.testing import CliRunner
from myapp.cli import app


def test_file_creation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "testproject"])
        assert result.exit_code == 0

        # 验证文件已创建
        from pathlib import Path
        assert Path("testproject/pyproject.toml").exists()
        assert Path("testproject/src").is_dir()
```

### 使用环境变量测试

```python
def test_respects_no_color():
    runner = CliRunner()
    result = runner.invoke(app, ["status"], env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    # 验证输出中没有 ANSI 转义码
    assert "\033[" not in result.output
```

### 快照测试

```python
import pytest
from syrupy.assertion import SnapshotAssertion
from typer.testing import CliRunner
from myapp.cli import app

runner = CliRunner()


def test_help_output(snapshot: SnapshotAssertion):
    result = runner.invoke(app, ["--help"])
    assert result.output == snapshot
```

## 最佳实践

1. **为所有内容编写 `--help`**。每个命令和选项都应该有清晰的帮助字符串。用户会在阅读文档之前先阅读它。

2. **支持 `--json` 输出**。机器可读输出使您的 CLI 可以与其他工具（`jq`、脚本、CI 管道）组合使用。

3. **将诊断信息写入 stderr**。使用 `stderr` 进行进度、警告和错误。将 `stdout` 保留用于数据输出：
   ```python
   import sys
   print("数据输出")              # stdout -- 可管道
   print("警告：...", file=sys.stderr)  # stderr -- 可见但不管道
   ```

4. **一致地使用退出码**。成功返回 0，错误返回非零。记录您的退出码。

5. **尊重 `NO_COLOR`**。检查 `NO_COLOR` 环境变量，并在设置时禁用颜色/格式化。

6. **使用 CliRunner 测试**。Click 和 Typer 都提供 `CliRunner` 进行测试，无需启动子进程。

7. **添加 shell 自动完成**。Typer 免费生成它。对于 Click，使用 `click-completion` 或 `click` 的内置支持。

8. **在 Typer 中使用 `Annotated` 参数**（而不是位置默认值），以实现更清晰、更易维护的代码。

9. **提供 `--verbose` 和 `--quiet` 标志**。让用户控制输出详细程度。考虑使用 Python 的 `logging` 模块并配置级别。

10. **版本标志**。始终提供 `--version`：
    ```python
    from importlib.metadata import version

    app = typer.Typer()

    def version_callback(value: bool) -> None:
        if value:
            typer.echo(f"myapp {version('my-package')}")
            raise typer.Exit()

    @app.callback()
    def main(
        version: Annotated[
            bool, typer.Option("--version", callback=version_callback, is_eager=True)
        ] = False,
    ) -> None:
        pass
    ```