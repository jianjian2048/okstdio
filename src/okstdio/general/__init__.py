"""通用模块

提供 JSON-RPC 通用模型和错误处理。
"""

from .jsonrpc_model import (
    BaseJSONRPC,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCErrorDetail,
    JSONRPCServerErrorDetail,
    JSONRPCError,
)
from .errors import (
    RPCError,
    RPCParseError,
    RPCInvalidRequestError,
    RPCMethodNotFoundError,
    RPCInvalidParamsError,
    RPCInternalError,
    RPCServerError,
)

__all__ = [
    "BaseJSONRPC",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCErrorDetail",
    "JSONRPCServerErrorDetail",
    "JSONRPCError",
    "RPCError",
    "RPCParseError",
    "RPCInvalidRequestError",
    "RPCMethodNotFoundError",
    "RPCInvalidParamsError",
    "RPCInternalError",
    "RPCServerError",
]
