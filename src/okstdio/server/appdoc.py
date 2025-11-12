"""应用程序文档"""

from __future__ import annotations  # type: ignore
import inspect
import json
from typing import TYPE_CHECKING, Callable, Any
from pathlib import Path
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from .router import RPCRouter
    from .application import RPCServer


# region 应用程序文档
class AppDoc:

    def docs_json(self: "RPCServer") -> dict:
        """生成当前服务的文档描述数据"""

        def is_pydantic_model(annotation: Any) -> bool:
            return isinstance(annotation, type) and issubclass(annotation, BaseModel)

        def serialize_params(func: Callable):
            params_data = []
            signature = inspect.signature(func)
            for param in signature.parameters.values():
                annotation = param.annotation

                # 跳过内部注入类型
                if (
                    annotation is not inspect._empty
                    and isinstance(annotation, type)
                    and annotation.__name__ == "IOWrite"
                ):
                    continue

                item: dict[str, Any] = {
                    "name": param.name,
                    "kind": param.kind.name,
                    "required": param.default is inspect._empty,
                }

                if annotation is inspect._empty:
                    item["type"] = None
                elif is_pydantic_model(annotation):
                    item["type"] = annotation.__name__
                    item["schema"] = annotation.model_json_schema()
                elif isinstance(annotation, type):
                    item["type"] = annotation.__name__
                else:
                    item["type"] = str(annotation)

                default = param.default
                if default is inspect._empty:
                    item["default"] = None
                else:
                    try:
                        json.dumps(default)
                        item["default"] = default
                    except TypeError:
                        item["default"] = repr(default)

                params_data.append(item)
            return params_data

        def is_custom_type(annotation: Any) -> bool:
            if not isinstance(annotation, type):
                return False
            return annotation.__module__ not in {"builtins", "typing"}

        def serialize_results(func: Callable):
            signature = inspect.signature(func)
            annotation = signature.return_annotation

            if annotation is inspect._empty or annotation is None:
                return []

            item: dict[str, Any] = {}
            if is_pydantic_model(annotation):
                item["type"] = annotation.__name__
                item["schema"] = annotation.model_json_schema()
            elif isinstance(annotation, type):
                item["type"] = annotation.__name__
            else:
                item["type"] = str(annotation)

            if isinstance(annotation, type) and is_custom_type(annotation):
                doc = inspect.getdoc(annotation) or ""
                if doc:
                    item["doc"] = doc

            return [item]

        def walk(router: RPCRouter, full_prefix: str = ""):
            methods = []
            for method_name, (func, label) in router.methods.items():
                path = ".".join(filter(None, [full_prefix, method_name]))
                methods.append(
                    {
                        "name": method_name,
                        "label": label,
                        "path": path,
                        "doc": inspect.getdoc(func) or "",
                        "params": serialize_params(func),
                        "results": serialize_results(func),
                    }
                )

            middlewares = []
            for middleware, label in getattr(router.middlewares, "get_full")():
                middlewares.append(
                    {
                        "name": middleware.__name__,
                        "label": label,
                        "doc": inspect.getdoc(middleware) or "",
                    }
                )

            routers = {}
            for prefix, sub_router in router.sub_routers.items():
                sub_prefix = ".".join(filter(None, [full_prefix, prefix]))
                routers[prefix] = walk(sub_router, sub_prefix)

            return {
                "label": getattr(router, "label", ""),
                "methods": methods,
                "middlewares": middlewares,
                "routers": routers,
            }

        tree = walk(self, "")
        return {
            "server_name": self.server_name,
            "version": self.version,
            "label": getattr(self, "label", ""),
            "methods": tree["methods"],
            "middlewares": tree["middlewares"],
            "routers": tree["routers"],
        }

    def docs_markdown(self: "RPCServer") -> str:
        """生成 Markdown 形式的接口文档."""

        doc = self.docs_json()
        lines: list[str] = []

        lines.append(f"# {doc['server_name'].upper()} API 文档")
        lines.append("")
        lines.append(f"- 版本: `{doc['version']}`")
        if doc.get("label"):
            lines.append(f"- 描述: {doc['label']}")
        lines.append("")

        if doc.get("middlewares"):
            lines.append("## 全局中间件")
            for mw in doc["middlewares"]:
                header = f"- **{mw['name']}**"
                if mw.get("label"):
                    header += f" `{mw['label']}`"
                lines.append(header)
                if mw.get("doc"):

                    doc_lines = str(mw["doc"]).strip().splitlines()
                    for i, dl in enumerate(doc_lines):
                        if i == 0:
                            lines.append(f"\n\t- {dl}")
                        else:
                            lines.append(f"\t\t{dl}")
                lines.append("")
            lines.append("")

        def render_params(params: list[dict[str, Any]]) -> None:
            if not params:
                lines.append("*无参数*")
                return
            lines.append("| 参数名 | 类型 | 必填 | 默认值 |")
            lines.append("| --- | --- | --- | --- |")
            for param in params:
                default = param.get("default")
                default_repr = (
                    "-" if default in (None, inspect._empty) else f"`{default}`"
                )
                required = "是" if param.get("required") else "否"
                lines.append(
                    f"| `{param['name']}` | {param.get('type') or '-'} | {required} | {default_repr} |"
                )
                schema = param.get("schema")
                if schema:
                    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
                    lines.append("")
                    lines.append("```json")
                    lines.append(schema_json)
                    lines.append("```")
            lines.append("")

        def render_results(results: list[dict[str, Any]]) -> None:
            if not results:
                lines.append("*无返回说明*")
                return
            lines.append("| 类型 | 说明 |")
            lines.append("| --- | --- |")
            for result in results:
                docstring = result.get("doc") or "-"
                lines.append(f"| {result.get('type', '-')} | {docstring} |")
                schema = result.get("schema")
                if schema:
                    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
                    lines.append("")
                    lines.append("```json")
                    lines.append(schema_json)
                    lines.append("```")
            lines.append("")

        def render_methods(methods: list[dict[str, Any]], heading_prefix: str) -> None:
            for method in methods:
                label = f" `{method['label']}`" if method.get("label") else ""
                lines.append(f"{heading_prefix} {method['path']}{label}")
                if method.get("doc"):
                    doc_lines = str(method["doc"]).strip().splitlines()
                    lines.extend(doc_lines)
                    lines.append("")
                lines.append("**参数**")
                render_params(method.get("params", []))
                lines.append("**返回**")
                render_results(method.get("results", []))

        # 顶层方法
        if doc.get("methods"):
            lines.append("## 顶层方法")
            render_methods(doc["methods"], "###")

        def render_router(name: str, router: dict, prefix: str = "") -> None:
            full_name = f"{prefix}.{name}" if prefix else name
            label = f" `{router['label']}`" if router.get("label") else ""
            lines.append(f"## 路由 {full_name}{label}")
            if router.get("methods"):
                render_methods(router["methods"], "###")
            if router.get("middlewares"):
                lines.append("**中间件**")
                for mw in router["middlewares"]:
                    header = f"- `{mw['name']}`"
                    if mw.get("label"):
                        header += f" `{mw['label']}`"
                    lines.append(header)
                    if mw.get("doc"):
                        doc_lines = str(mw["doc"]).strip().splitlines()
                        for dl in doc_lines:
                            lines.append(f"  {dl}")
                lines.append("")
            for child_name, child_router in router.get("routers", {}).items():
                render_router(child_name, child_router, full_name)

        for router_name, router in doc.get("routers", {}).items():
            render_router(router_name, router)

        with open(f"{self.server_name}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines).strip())
