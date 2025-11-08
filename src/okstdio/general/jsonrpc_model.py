from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Any
from .errors import RPCInvalidRequestError


# region BaseJSONRPC
class BaseJSONRPC(BaseModel):

    id: int | str = Field(default=0, description="请求ID")
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")

    @field_validator("jsonrpc", mode="before")
    @classmethod
    def validate_jsonrpc(cls, v, info) -> str:
        if v != "2.0":
            raise RPCInvalidRequestError(from_id=info.data.get("id", 0))
        return v.upper()

    def __str__(self):
        return self.model_dump_json()


class JSONRPCRequest(BaseJSONRPC):
    method: str = Field(description="请求方法")
    params: Any = Field(description="请求参数")


class JSONRPCResponse(BaseJSONRPC):
    result: Any = Field(description="响应结果")


class RPCErrorDetail(BaseModel):
    code: int = Field(description="错误码")
    message: str = Field(description="错误信息")
    data: dict | list | None = Field(default=None, description="错误数据")


class JSONRPCError(BaseJSONRPC):
    error: RPCErrorDetail = Field(description="错误详情")
