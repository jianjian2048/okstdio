"""参数编辑器组件

用于编辑 JSON-RPC 请求参数的 TextArea 组件。
"""

import json
from typing import Any
from textual.widgets import TextArea, Static
from textual.containers import Vertical
from textual.message import Message


def generate_params_template(params: list[dict[str, Any]]) -> str:
    """根据参数信息生成 JSON 模板

    Args:
        params: 参数列表，来自方法信息的 params 字段

    Returns:
        str: JSON 格式的参数模板字符串
    """
    template: dict[str, Any] = {}

    for param in params:
        name = param.get("name", "")
        param_type = param.get("type", "any")
        required = param.get("required", False)
        default = param.get("default")

        if required:
            # 必填参数：生成类型提示占位符
            template[name] = _get_type_hint_value(param_type)
        elif default is not None:
            # 有默认值：使用默认值
            template[name] = default
        else:
            # 可选参数：使用类型提示
            template[name] = _get_type_hint_value(param_type)

    if not template:
        return "{}"

    return json.dumps(template, indent=2, ensure_ascii=False)


def _get_type_hint_value(type_name: str | None) -> Any:
    """根据类型名生成占位符值

    Args:
        type_name: 类型名称

    Returns:
        对应类型的占位符值
    """
    if type_name is None:
        return None

    type_lower = type_name.lower()

    if type_lower in ("int", "integer"):
        return 0
    elif type_lower in ("float", "double", "number"):
        return 0.0
    elif type_lower in ("str", "string"):
        return ""
    elif type_lower in ("bool", "boolean"):
        return False
    elif type_lower in ("list", "array"):
        return []
    elif type_lower in ("dict", "object"):
        return {}
    else:
        # 自定义类型，使用 null 占位
        return None


class MethodHeader(Static):
    """方法标题组件

    显示当前选中方法的名称和标签。
    """

    def __init__(self, **kwargs) -> None:
        """初始化方法标题"""
        super().__init__("", **kwargs)
        self._method_name = ""
        self._method_label = ""

    def update_method(self, name: str, label: str = "") -> None:
        """更新方法信息

        Args:
            name: 方法名称
            label: 方法标签
        """
        self._method_name = name
        self._method_label = label

        if label:
            self.update(f"Method: [bold]{name}[/bold] [{label}]")
        else:
            self.update(f"Method: [bold]{name}[/bold]")


class ParamsEditor(Vertical):
    """参数编辑器容器

    包含方法标题和 JSON 编辑器。

    消息:
        ParamsChanged: 当参数内容改变时触发

    例子:
        ```python
        editor = ParamsEditor()
        editor.set_method("hello", "问候方法", params_info)

        # 获取参数
        params = editor.get_params()
        ```
    """

    class ParamsChanged(Message):
        """参数改变消息"""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, **kwargs) -> None:
        """初始化参数编辑器"""
        super().__init__(**kwargs)
        self._current_method: str = ""

    def compose(self):
        """创建子组件"""
        yield MethodHeader(id="method-header")
        yield TextArea(
            "{}",
            id="params-input",
            language="json",
            soft_wrap=True
        )

    def set_method(
        self,
        method_name: str,
        method_label: str,
        params: list[dict[str, Any]]
    ) -> None:
        """设置当前方法

        Args:
            method_name: 方法名称
            method_label: 方法标签
            params: 参数信息列表
        """
        self._current_method = method_name

        # 更新标题
        header = self.query_one("#method-header", MethodHeader)
        header.update_method(method_name, method_label)

        # 生成参数模板
        template = generate_params_template(params)

        # 更新编辑器
        textarea = self.query_one("#params-input", TextArea)
        textarea.text = template

    def get_params_text(self) -> str:
        """获取参数文本

        Returns:
            str: JSON 格式的参数文本
        """
        textarea = self.query_one("#params-input", TextArea)
        return textarea.text

    def get_params(self) -> dict[str, Any]:
        """解析并返回参数字典

        Returns:
            dict: 解析后的参数字典

        Raises:
            json.JSONDecodeError: 当 JSON 格式错误时
        """
        text = self.get_params_text()
        return json.loads(text) if text.strip() else {}

    def set_params(self, params: dict[str, Any]) -> None:
        """设置参数

        Args:
            params: 参数字典
        """
        textarea = self.query_one("#params-input", TextArea)
        textarea.text = json.dumps(params, indent=2, ensure_ascii=False)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """文本改变事件处理"""
        if event.text_area.id == "params-input":
            self.post_message(self.ParamsChanged(event.text_area.text))
