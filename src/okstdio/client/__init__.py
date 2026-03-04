"""RPC 客户端模块

提供基于 Stdio 的 JSON-RPC 客户端实现，用于与子进程进行通信。
"""

from .application import RPCClient

__all__ = ["RPCClient"]
