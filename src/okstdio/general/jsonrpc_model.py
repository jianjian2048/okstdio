"""JSON-RPC 模型定义

提供 JSON-RPC 2.0 协议的核心数据模型。
"""

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Any
from .errors import RPCInvalidRequestError


class BaseJSONRPC(BaseModel):
    """JSON-RPC 基础模型
    
    所有 JSON-RPC 消息的基类，包含 id 和 jsonrpc 字段。
    
    Args:
        id: 请求 ID，可以是整数或字符串
        jsonrpc: JSON-RPC 版本，必须为 "2.0"
    
    Raises:
        RPCInvalidRequestError: 当 jsonrpc 版本不是 "2.0" 时
    """

    id: int | str = Field(default=0, description="请求ID")
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")

    @field_validator("jsonrpc", mode="before")
    @classmethod
    def validate_jsonrpc(cls, v, info) -> str:
        """验证 JSON-RPC 版本
        
        Args:
            v: jsonrpc 版本值
            info: Pydantic 验证信息
        
        Returns:
            str: 验证后的 jsonrpc 版本
        
        Raises:
            RPCInvalidRequestError: 当版本不是 "2.0" 时
        """
        if v != "2.0":
            raise RPCInvalidRequestError(from_id=info.data.get("id", 0))
        return v

    def encode(self, encoding: str = "utf-8"):
        """编码为字节
        
        Args:
            encoding: 编码格式，默认 "utf-8"
        
        Returns:
            bytes: 编码后的字节数据
        """
        return self.model_dump_json().encode(encoding)


class JSONRPCRequest(BaseJSONRPC):
    """JSON-RPC 请求模型
    
    用于表示 JSON-RPC 请求消息。
    
    Args:
        id: 请求 ID
        jsonrpc: JSON-RPC 版本
        method: 请求方法名称
        params: 请求参数
    
    例子：
        ```json
        {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "hello",
            "params": {"name": "World"}
        }
        ```
    """

    method: str = Field(description="请求方法")
    params: Any = Field(description="请求参数")


class JSONRPCResponse(BaseJSONRPC):
    """JSON-RPC 响应模型
    
    用于表示成功的 JSON-RPC 响应消息。
    
    Args:
        id: 请求 ID
        jsonrpc: JSON-RPC 版本
        result: 响应结果
    
    例子：
        ```json
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": {"message": "Hello, World!"}
        }
        ```
    """

    result: Any = Field(description="响应结果")


class JSONRPCErrorDetail(BaseModel):
    """JSON-RPC 错误详情模型
    
    用于表示 JSON-RPC 错误信息。
    
    Args:
        code: 错误码
        message: 错误信息
        data: 错误数据（可选）
    """

    code: int = Field(description="错误码")
    message: str = Field(description="错误信息")
    data: dict | list | None = Field(default=None, description="错误数据")


class JSONRPCServerErrorDetail(JSONRPCErrorDetail):
    """JSON-RPC 服务器错误详情模型
    
    用于表示服务器自定义错误，错误码范围为 -32000 到 -32099。
    
    Args:
        code: 错误码，默认 -32000，范围 -32099 到 -32000
        message: 错误信息
        data: 错误数据（可选）
    """

    code: int = Field(-32000, ge=-32099, le=-32000, description="错误码")


class JSONRPCError(BaseJSONRPC):
    """JSON-RPC 错误模型
    
    用于表示 JSON-RPC 错误响应消息。
    
    Args:
        id: 请求 ID
        jsonrpc: JSON-RPC 版本
        error: 错误详情
    
    例子：
        ```json
        {
            "id": 1,
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": null
            }
        }
        ```
    """

    error: JSONRPCErrorDetail = Field(description="错误详情")
