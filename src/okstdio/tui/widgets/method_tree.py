"""方法树组件

展示服务器方法树的 Tree 组件。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from textual.widgets import Tree
from textual.message import Message


@dataclass
class MethodNode:
    """方法树节点数据

    Args:
        path: 完整方法路径，如 "server.sub.method"
        method_info: 原始方法信息字典
        is_router: 是否为路由节点
    """

    path: str
    method_info: dict[str, Any] | None
    is_router: bool


class MethodTreeWidget(Tree[MethodNode]):
    """方法树组件

    基于 Tree 组件，递归展示服务器方法树结构。

    消息:
        MethodSelected: 当用户选择一个方法时触发

    例子:
        ```python
        tree = MethodTreeWidget()
        tree.update_tree(method_tree_data)

        # 监听方法选择事件
        def on_method_tree_widget_method_selected(event):
            print(f"选中方法: {event.method_info['path']}")
        ```
    """

    class MethodSelected(Message):
        """方法选中消息

        Args:
            method_info: 方法信息字典
        """

        def __init__(self, method_info: dict[str, Any]) -> None:
            self.method_info = method_info
            super().__init__()

    def __init__(self, label: str = "Server", **kwargs) -> None:
        """初始化方法树

        Args:
            label: 根节点标签
            **kwargs: 传递给 Tree 的其他参数
        """
        super().__init__(label, **kwargs)
        self._method_tree: dict[str, Any] = {}

    def update_tree(self, method_tree: dict[str, Any]) -> None:
        """更新方法树数据

        Args:
            method_tree: 从 get_server_methods() 获取的方法树数据
        """
        self._method_tree = method_tree
        self.clear()

        root = self.root
        root.set_label(f"{method_tree.get('server_name', 'Server')} [{method_tree.get('version', '')}]")
        root.data = MethodNode(
            path=method_tree.get("server_name", ""),
            method_info=None,
            is_router=True
        )

        # 递归添加方法
        self._add_methods(root, method_tree.get("methods", []))

        # 递归添加路由器
        self._add_routers(root, method_tree.get("routers", {}), method_tree.get("server_name", ""))

        # 展开根节点
        root.expand()

    def _add_methods(
        self,
        parent,  # type: Tree.Node[MethodNode]
        methods: list[dict[str, Any]]
    ) -> None:
        """添加方法节点

        Args:
            parent: 父节点
            methods: 方法列表
        """
        for method in methods:
            node = parent.add(
                method["name"],
                data=MethodNode(
                    path=method["path"],
                    method_info=method,
                    is_router=False
                )
            )
            # 方法节点不允许展开
            node.allow_expand = False

    def _add_routers(
        self,
        parent,  # type: Tree.Node[MethodNode]
        routers: dict[str, dict[str, Any]],
        prefix: str
    ) -> None:
        """递归添加路由器节点

        Args:
            parent: 父节点
            routers: 路由器字典
            prefix: 路径前缀
        """
        for router_name, router_info in routers.items():
            path = f"{prefix}.{router_name}" if prefix else router_name

            # 创建路由节点
            router_node = parent.add(
                f"📁 {router_name}",
                data=MethodNode(
                    path=path,
                    method_info=None,
                    is_router=True
                )
            )

            # 添加方法
            self._add_methods(router_node, router_info.get("methods", []))

            # 递归添加子路由器
            self._add_routers(router_node, router_info.get("routers", {}), path)

    def on_tree_node_selected(self, event: Tree.NodeSelected[MethodNode]) -> None:
        """节点选中事件处理

        Args:
            event: 节点选中事件
        """
        node = event.node
        if node.data and not node.data.is_router and node.data.method_info:
            self.post_message(self.MethodSelected(node.data.method_info))