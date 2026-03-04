"""错误处理模块

提供 JSON-RPC 标准错误和自定义错误类。
所有错误类都继承自 RPCError 基类，支持错误码、错误消息和错误数据。
"""

from typing import Any


"""
JSON-RPC 2.0 错误码规范：

code            message                     meaning
--------------------------------------------------------------
-32700          Parse error                 服务端接收到无效的 json。该错误发送于服务器尝试解析json文本。
-32600          Invalid Request             发送的json不是一个有效的请求对象。
-32601          Method not found            该方法不存在或无效。
-32602          Invalid params              无效的方法参数。
-32603          Internal error              JSON-RPC内部错误。
-32000 to -32099 Server error               预留用于自定义的服务器错误。
"""


class RPCError(Exception):
    """RPC 异常基类
    
    所有 JSON-RPC 错误的基类，支持标准的错误码、错误消息和可选的错误数据。
    
    Args:
        code: 错误码，符合 JSON-RPC 2.0 规范
        message: 错误信息
        data: 错误数据，可以是 dict、list 或 None
        from_id: 请求 ID，默认 0
    
    例子：
        ```python
        # 使用自定义错误
        raise RPCError(
            code=-32001,
            message="资源不存在",
            data={"resource_id": 123},
            from_id="req-001"
        )
        
        # 转换为字典
        error = RPCError(-32001, "错误信息")
        error_dict = error.to_dict()
        # {"code": -32001, "message": "错误信息"}
        ```
    """

    def __init__(self, code: int, message: str, data: Any = None, from_id: Any = 0):
        """初始化 RPC 异常
        
        Args:
            code: 错误码
            message: 错误信息
            data: 错误数据 [dict | list | None]
            from_id: 请求ID [int | str ] 默认 0
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
        self.from_id = from_id

    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含 code、message 和可选 data 的字典
        """
        error = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return error


class RPCParseError(RPCError):
    """语法解析错误
    
    当服务器接收到无效的 JSON 时抛出。
    对应 JSON-RPC 2.0 错误码：-32700
    
    例子：
        ```python
        # 当请求体不是有效 JSON 时自动抛出
        try:
            # 处理请求
            pass
        except RPCParseError as e:
            print(f"JSON 解析失败: {e.message}")
        ```
    """

    def __init__(self, data: Any = None, from_id: Any = 0):
        """初始化语法解析错误
        
        Args:
            data: 错误数据
            from_id: 请求 ID
        """
        self.code = -32700
        self.message = "PARSE_ERROR - [语法解析错误]"
        super().__init__(self.code, self.message, data, from_id)


class RPCInvalidRequestError(RPCError):
    """无效请求错误
    
    当发送的 JSON 不是一个有效的请求对象时抛出。
    对应 JSON-RPC 2.0 错误码：-32600
    
    例子：
        ```python
        # 当缺少必需字段时抛出
        raise RPCInvalidRequestError(
            data={"missing_fields": ["method", "id"]},
            from_id="req-001"
        )
        ```
    """

    def __init__(self, data: Any = None, from_id: Any = 0):
        """初始化无效请求错误
        
        Args:
            data: 错误数据
            from_id: 请求 ID
        """
        self.code = -32600
        self.message = "INVALID_REQUEST - [无效请求错误]"
        super().__init__(self.code, self.message, data, from_id)


class RPCMethodNotFoundError(RPCError):
    """方法未找到错误
    
    当请求的方法不存在或无效时抛出。
    对应 JSON-RPC 2.0 错误码：-32601
    
    例子：
        ```python
        # 当路由未注册时抛出
        raise RPCMethodNotFoundError(
            data={"method": "unknown.method"},
            from_id="req-001"
        )
        ```
    """

    def __init__(self, data: Any = None, from_id: Any = 0):
        """初始化方法未找到错误
        
        Args:
            data: 错误数据
            from_id: 请求 ID
        """
        self.code = -32601
        self.message = "METHOD_NOT_FOUND - [找不到方法错误]"
        super().__init__(self.code, self.message, data, from_id)


class RPCInvalidParamsError(RPCError):
    """无效参数错误
    
    当方法参数无效时抛出（如类型不匹配、验证失败等）。
    对应 JSON-RPC 2.0 错误码：-32602
    
    例子：
        ```python
        # 当 Pydantic 验证失败时自动抛出
        try:
            # 处理请求
            pass
        except RPCInvalidParamsError as e:
            print(f"参数验证失败: {e.data}")
        ```
    """

    def __init__(self, data: Any = None, from_id: Any = 0):
        """初始化无效参数错误
        
        Args:
            data: 错误数据（通常包含验证错误详情）
            from_id: 请求 ID
        """
        self.code = -32602
        self.message = "INVALID_PARAMS - [无效参数错误]"
        super().__init__(self.code, self.message, data, from_id)


class RPCInternalError(RPCError):
    """内部错误
    
    当发生 JSON-RPC 内部错误时抛出。
    对应 JSON-RPC 2.0 错误码：-32603
    
    例子：
        ```python
        # 当处理过程中发生未预期的错误时
        try:
            # 处理请求
            pass
        except Exception as e:
            raise RPCInternalError(
                data={"error": str(e)},
                from_id="req-001"
            )
        ```
    """

    def __init__(self, data: Any = None, from_id: Any = 0):
        """初始化内部错误
        
        Args:
            data: 错误数据
            from_id: 请求 ID
        """
        self.code = -32603
        self.message = "INTERNAL_ERROR - [内部错误]"
        super().__init__(self.code, self.message, data, from_id)


class RPCServerError(RPCError):
    """服务器自定义错误
    
    用于服务器自定义的错误，错误码范围为 -32000 到 -32099。
    
    Args:
        code: 错误码，范围 -32000 到 -32099
        message: 错误信息
        data: 错误数据 [dict | list | None]
        from_id: 请求ID [int | str ] 默认 0
    
    例子：
        ```python
        # 自定义业务错误
        raise RPCServerError(
            code=-32001,
            message="资源不存在",
            data={"resource_id": 123},
            from_id="req-001"
        )
        
        raise RPCServerError(
            code=-32002,
            message="权限不足",
            from_id="req-001"
        )
        ```
    """

    def __init__(self, code: int, message: str, data: Any = None, from_id: Any = 0):
        """初始化服务器自定义错误
        
        Args:
            code: 错误码 范围 -32000 到 -32099
            message: 错误信息
            data: 错误数据 [dict | list | None]
            from_id: 请求ID [int | str ] 默认 0
        """
        self.code = -32000 if code < -32000 else -32099 if code > -32099 else code
        self.message = message or "SERVER_ERROR - [服务端错误]"
        super().__init__(self.code, self.message, data, from_id)
