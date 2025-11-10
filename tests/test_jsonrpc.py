from okstdio.general.jsonrpc_model import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    RPCErrorDetail,
)
from okstdio.general.errors import RPCError
from pydantic import ValidationError


if __name__ == "__main__":
    # try:
    #     json_data = '{"jsonrpc": "1.0", "method": "test", "params": {"name": "test", "age": 18}, "id": 10}'
    #     request = JSONRPCRequest.model_validate_json(json_data)
    #     print(request)
    # except RPCError as exc:
    #     error = RPCErrorDetail.model_validate(exc.to_dict())
    #     response = JSONRPCError(error=error, id=exc.from_id)
    #     print(response)
    # # except ValidationError as exc:
    # #     # error = RPCErrorDetail(code=-32600, message="Invalid Request", data=exc.errors())
    # #     print(exc.json(include_url=False, include_input=False, include_context=False))
    # else:
    #     print(request)

    # try:
    #     response = JSONRPCResponse(jsonrpc="2.0", result="test", id=1)
    # except ValidationError as exc:
    #     print(exc.errors(include_url=False))
    # else:
    #     print(response)

    test_res = JSONRPCResponse(result={"a": "abc"})
    print(test_res.encode("utf-8") + b"\n")
