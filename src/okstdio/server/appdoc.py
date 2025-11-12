"""应用程序文档"""

from __future__ import annotations  # type: ignore
import inspect
import json
from typing import TYPE_CHECKING, Callable, Any, get_origin, get_args
from pathlib import Path
from pydantic import BaseModel
from pydantic.fields import FieldInfo
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
                field_info = None

                # 跳过内部注入类型
                if (
                    annotation is not inspect._empty
                    and isinstance(annotation, type)
                    and annotation.__name__ == "IOWrite"
                ):
                    continue

                # 处理 Annotated 类型
                if get_origin(annotation) is not None:
                    # 尝试从 Annotated 中提取 FieldInfo
                    args = get_args(annotation)
                    if args:
                        # 第一个参数是实际类型
                        real_type = args[0]
                        # 查找 FieldInfo
                        for arg in args[1:]:
                            if isinstance(arg, FieldInfo):
                                field_info = arg
                                break
                        annotation = real_type

                item: dict[str, Any] = {
                    "name": param.name,
                    "kind": param.kind.name,
                    "required": param.default is inspect._empty,
                }

                # 如果有 FieldInfo，优先使用其中的描述信息
                if field_info:
                    item["description"] = field_info.description or ""

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

        def get_class_own_doc(cls: type) -> str:
            """获取类自己定义的 docstring, 不包括继承来的"""
            if not isinstance(cls, type):
                return ""
            # 只有在类的 __dict__ 中直接定义了 __doc__ 才返回
            if "__doc__" in cls.__dict__ and cls.__dict__["__doc__"]:
                return cls.__dict__["__doc__"].strip()
            return ""

        def serialize_results(func: Callable):
            signature = inspect.signature(func)
            annotation = signature.return_annotation

            if annotation is inspect._empty or annotation is None:
                return []

            # 处理联合类型 (A | B)
            origin = get_origin(annotation)
            if origin is not None:
                import types

                # UnionType 是 Python 3.10+ 的 X | Y 语法
                if origin is types.UnionType or str(origin) == "typing.Union":
                    args = get_args(annotation)
                    results = []
                    for arg in args:
                        if arg is type(None):  # 跳过 None
                            continue
                        result_item: dict[str, Any] = {}
                        if is_pydantic_model(arg):
                            result_item["type"] = arg.__name__
                            result_item["schema"] = arg.model_json_schema()
                        elif isinstance(arg, type):
                            result_item["type"] = arg.__name__
                        else:
                            result_item["type"] = str(arg)

                        # 只获取类自己的 docstring
                        if isinstance(arg, type) and is_custom_type(arg):
                            doc = get_class_own_doc(arg)
                            if doc:
                                result_item["doc"] = doc

                        results.append(result_item)
                    return results

            # 单一返回类型
            item: dict[str, Any] = {}
            if is_pydantic_model(annotation):
                item["type"] = annotation.__name__
                item["schema"] = annotation.model_json_schema()
            elif isinstance(annotation, type):
                item["type"] = annotation.__name__
            else:
                item["type"] = str(annotation)

            # 只获取类自己的 docstring
            if isinstance(annotation, type) and is_custom_type(annotation):
                doc = get_class_own_doc(annotation)
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
                header = f"### {mw['name']}"
                if mw.get("label"):
                    header += f" `{mw['label']}`"
                lines.append(header)
                if mw.get("doc"):

                    doc_lines = str(mw["doc"]).strip().splitlines()
                    for i, dl in enumerate(doc_lines):
                        if i == 0:
                            lines.append(f"\n> {dl}")
                        else:
                            lines.append(f"> {dl}")
                lines.append("")
            lines.append("")

        def render_params(params: list[dict[str, Any]]) -> None:
            if not params:
                lines.append("> *无参数*")
                lines.append("")
                return

            lines.append("> | 参数名 | 类型 | 必填 | 默认值 | 描述 |")
            lines.append("> | --- | --- | --- | --- | --- |")
            for param in params:
                default = param.get("default")
                default_repr = (
                    "-" if default in (None, inspect._empty) else f"`{default}`"
                )
                required = "是" if param.get("required") else "否"
                description = param.get("description", "-")
                lines.append(
                    f"> | `{param['name']}` | {param.get('type') or '-'} | {required} | {default_repr} | {description} |"
                )

                # 如果参数有 schema，展示其字段表格
                schema = param.get("schema")
                if schema:
                    lines.append(">")
                    lines.append(f"> **`{param['name']}` 字段:**")
                    lines.append(">")
                    schema_table = schema_to_table(schema)
                    if schema_table:
                        for line in schema_table:
                            if line:  # 跳过空行
                                lines.append(f"> {line}")
                            else:
                                lines.append(">")
            lines.append("")

        def schema_to_table(schema: dict) -> list[str]:
            """将 JSON Schema 转换为易读的表格"""
            table_lines = []
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])

            if not properties:
                return []

            table_lines.append("")
            table_lines.append("| 字段名 | 类型 | 必填 | 默认值 | 描述 |")
            table_lines.append("| --- | --- | --- | --- | --- |")

            for field_name, field_schema in properties.items():
                # 判断是否必填
                is_required = "是" if field_name in required_fields else "否"

                # 获取类型
                field_type = field_schema.get("type", "")
                if "anyOf" in field_schema:
                    # 处理联合类型 - 使用 / 而不是 | 避免表格分隔符冲突
                    types = []
                    for item in field_schema["anyOf"]:
                        if item.get("type") == "null":
                            types.append("null")
                        elif "$ref" in item:
                            types.append(item["$ref"].split("/")[-1])
                        else:
                            types.append(item.get("type", "unknown"))
                    field_type = " / ".join(types)
                elif "$ref" in field_schema:
                    field_type = field_schema["$ref"].split("/")[-1]
                elif field_type == "array":
                    items = field_schema.get("items", {})
                    if "$ref" in items:
                        field_type = f"array[{items['$ref'].split('/')[-1]}]"
                    else:
                        field_type = f"array[{items.get('type', 'any')}]"

                # 获取默认值
                default = field_schema.get("default")
                if default is None and "null" not in str(field_type):
                    default_repr = "-"
                elif default is None:
                    default_repr = "`null`"
                else:
                    try:
                        default_repr = f"`{json.dumps(default, ensure_ascii=False)}`"
                    except:
                        default_repr = f"`{default}`"

                # 获取描述
                description = field_schema.get("description", "-")

                # 添加约束信息
                constraints = []
                if "minimum" in field_schema:
                    constraints.append(f"最小: {field_schema['minimum']}")
                if "maximum" in field_schema:
                    constraints.append(f"最大: {field_schema['maximum']}")
                if "minLength" in field_schema:
                    constraints.append(f"最短: {field_schema['minLength']}")
                if "maxLength" in field_schema:
                    constraints.append(f"最长: {field_schema['maxLength']}")
                if "const" in field_schema:
                    constraints.append(f"常量: {field_schema['const']}")

                if constraints:
                    description += f" ({', '.join(constraints)})"

                table_lines.append(
                    f"| `{field_name}` | {field_type} | {is_required} | {default_repr} | {description} |"
                )

            return table_lines

        def render_results(results: list[dict[str, Any]]) -> None:
            if not results:
                lines.append("> *无返回说明*")
                lines.append("")
                return

            for idx, result in enumerate(results):
                lines.append("> **类型:** `" + result.get("type", "-") + "`")
                lines.append(">")

                docstring = result.get("doc")
                if docstring:
                    lines.append("> **说明:**")
                    # 将 docstring 的每一行都加上 > 前缀
                    for doc_line in docstring.split("\n"):
                        lines.append(f">> {doc_line}")
                    lines.append(">")

                schema = result.get("schema")
                if schema:
                    schema_table = schema_to_table(schema)
                    if schema_table:
                        lines.append("> **字段:**")
                        for line in schema_table:
                            if line:  # 跳过空行
                                lines.append(f">> {line}")
                            else:
                                lines.append(">")

                    # 如果有 $defs，也展示引用的模型
                    defs = schema.get("$defs", {})
                    if defs:
                        for def_name, def_schema in defs.items():
                            lines.append(">>")
                            lines.append(f">> **引用模型: `{def_name}`**")
                            lines.append(">>")
                            def_table = schema_to_table(def_schema)
                            if def_table:
                                for line in def_table:
                                    if line:
                                        lines.append(f">>> {line}")
                                    else:
                                        lines.append(">>")

                # 如果不是最后一个结果，添加分隔线
                if idx < len(results) - 1:
                    lines.append(">")
                    lines.append("> ---")

            lines.append("")

        def render_methods(methods: list[dict[str, Any]], heading_prefix: str) -> None:
            for method in methods:
                label = f" `{method['label']}`" if method.get("label") else ""
                lines.append(f"{heading_prefix} {method['path']}{label}")
                if method.get("doc"):
                    doc_lines = str(method["doc"]).strip().splitlines()
                    for doc_line in doc_lines:
                        lines.append(f"> {doc_line}")
                    lines.append("")
                lines.append("**参数:**")
                lines.append("")
                render_params(method.get("params", []))
                lines.append("**返回:**")
                lines.append("")
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
