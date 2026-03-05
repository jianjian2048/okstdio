from okstdio.server.application import RPCServer, RPCRouter
from pydantic import Field
from typing import Annotated
import logging
from logging.handlers import RotatingFileHandler

LOG_HANDLER = RotatingFileHandler(
    filename="app.log", maxBytes=2 * 1024 * 1024, encoding="utf-8"
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers.clear()
root_logger.addHandler(LOG_HANDLER)


app = RPCServer("test_server", label="测试服务器", version="v1.0.0")


@app.add_method(name="hello")
def hello(name: Annotated[str, Field(description="姓名")]) -> str:
    """问候方法"""
    root_logger.info(f"收到方法调用：{name}")
    return f"Hello, {name}!"


sub_router = RPCRouter(prefix="sub", label="子路由")


@sub_router.add_method(name="user", label="用户详情")
def user_detail(user_id: Annotated[int, Field(description="用户ID")]) -> str:
    """用户详情"""
    return f"用户详情 {user_id} 用户详情"


app.include_router(sub_router)

if __name__ == "__main__":
    # print("开始启动测试服务器")
    app.runserver()
