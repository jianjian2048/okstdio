import asyncio
import sys
from pathlib import Path
from okstdio.server.application import RPCServer, RPCRouter, IOWrite
from okstdio.general.jsonrpc_model import (
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCServerErrorDetail,
)
from okstdio.server.application import RPCInvalidRequestError

from pydantic import Field
from typing import Annotated
import logging
from logging.handlers import RotatingFileHandler

# 添加环境父文件夹到 path
parent_path = Path(__file__).resolve().parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

from test_schema import TestTask, TestTaskMessage

# ==================== 日志配置 ====================
# 重要：日志只能写入文件，不能输出到 stdout
# 否则会干扰 JSON-RPC 通信
FORMAT = "[%(asctime)s] %(levelname)s @%(name)s > %(message)s"
DATEFMT = "%m-%d %H:%M:%S"
LOG_HANDLER = RotatingFileHandler(
    filename=".logs/app.log",
    maxBytes=2 * 1024 * 1024,  # 2MB
    backupCount=1,  # 保留 1 个备份
    encoding="utf-8",
)
LOG_HANDLER.setFormatter(logging.Formatter(FORMAT, DATEFMT))

# 配置 root logger，确保不输出到 stdout
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()  # 清除所有默认 handler(包括 StreamHandler）
root_logger.addHandler(LOG_HANDLER)

SERVER_NAME = "test_server"

logger = logging.getLogger(SERVER_NAME)

app = RPCServer(SERVER_NAME, label="测试服务器", version="v1.0.0")


@app.add_method(name="healthy", label="健康检查")
def healthy() -> dict:
    """问候方法"""
    return {"status": "healthy"}


@app.add_method(name="hello", label="问候方法")
def hello(name: str = "World") -> str:
    """问候方法"""
    return f"hello {name} !"


async def background_task(
    task_id: Annotated[str, Field(description="任务的ID")],
    io_write: IOWrite,
) -> None:

    for i in range(10):
        task_message = TestTaskMessage(message=f"任务进度 {(i+1)*10} %")
        if i == 9:
            task_message.task_completed = True
        response = JSONRPCResponse(
            id=task_id,
            result=task_message,
        )
        await io_write.write(response)
        await asyncio.sleep(1)


@app.add_method(name="test_background", label="测试后台任务")
async def test_background(io_write: IOWrite) -> TestTask:
    """测试后台任务"""

    task_info = TestTask()

    # 创建 后台任务
    asyncio.create_task(background_task(task_info.task_id, io_write))

    return task_info


@app.add_method(name="test_error", label="测试错误")
def test_error() -> JSONRPCServerErrorDetail:
    """测试错误"""

    return JSONRPCServerErrorDetail(
        code=-32001,
        message="测试错误",
        data={"param": "value"},
    )


if __name__ == "__main__":
    # print("开始启动测试服务器")
    app.runserver()
