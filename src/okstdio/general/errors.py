from typing import Any


"""
code	            message	                    meaning
--------------------------------------------------------------
-32700	            Parse error语法解析错误	    服务端接收到无效的 json。该错误发送于服务器尝试解析json文本。
-32600	            Invalid Request无效请求	    发送的json不是一个有效的请求对象。
-32601	            Method not found找不到方法	该方法不存在或无效。
-32602	            Invalid params无效的参数	无效的方法参数。
-32603	            Internal error内部错误	    JSON-RPC内部错误。
-32000 to -32099	Server error服务端错误	    预留用于自定义的服务器错误。
"""


# region RPC Error
class RPCError(Exception):
    """RPC 异常
    Args:
        code: 错误码
        message: 错误信息
        data: 错误数据 [dict | list | None]
        from_id: 请求ID [int | str ] 默认 0
    """

    def __init__(self, code: int, message: str, data: Any = None, from_id: Any = 0):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
        self.from_id = from_id

    def to_dict(self):
        error = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return error


# region 语法解析错误
class RPCParseError(RPCError):
    """语法解析错误"""

    def __init__(self, data: Any = None, from_id: Any = 0):
        self.code = -32700
        self.message = "PARSE_ERROR - [语法解析错误]"
        super().__init__(self.code, self.message, data, from_id)


# region 无效请求错误
class RPCInvalidRequestError(RPCError):
    """无效请求错误"""

    def __init__(self, data: Any = None, from_id: Any = 0):
        self.code = -32600
        self.message = "INVALID_REQUEST - [无效请求错误]"
        super().__init__(self.code, self.message, data, from_id)


# region 找不到方法错误
class RPCMethodNotFoundError(RPCError):
    """找不到方法错误"""

    def __init__(self, data: Any = None, from_id: Any = 0):
        self.code = -32601
        self.message = "METHOD_NOT_FOUND - [找不到方法错误]"
        super().__init__(self.code, self.message, data, from_id)


# region 无效参数错误
class RPCInvalidParamsError(RPCError):
    """无效参数错误"""

    def __init__(self, data: Any = None, from_id: Any = 0):
        self.code = -32602
        self.message = "INVALID_PARAMS - [无效参数错误]"
        super().__init__(self.code, self.message, data, from_id)


# region 内部错误
class RPCInternalError(RPCError):
    """内部错误"""

    def __init__(self, data: Any = None, from_id: Any = 0):
        self.code = -32603
        self.message = "INTERNAL_ERROR - [内部错误]"
        super().__init__(self.code, self.message, data, from_id)


# region 其他服务端错误
class RPCServerError(RPCError):
    """其他服务端错误
    Args:
        code: 错误码 范围 -32000 到 -32099
        message: 错误信息
        data: 错误数据 [dict | list | None]
        from_id: 请求ID [int | str ] 默认 0
    """

    def __init__(self, code: int, message: str, data: Any = None, from_id: Any = 0):
        self.code = -32000 if code < -32000 else -32099 if code > -32099 else code
        self.message = message or "SERVER_ERROR - [服务端错误]"
        super().__init__(self.code, self.message, data, from_id)
