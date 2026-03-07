import asyncio
import sys
from pathlib import Path
from okstdio.client import RPCClient
from okstdio.general.errors import RPCError
from rich import print
import logging

# 添加环境父文件夹到 path
parent_path = Path(__file__).resolve().parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

from test_schema import TestTask, TestTaskMessage


logging.basicConfig(level=logging.INFO)


async def test_client():

    # 构造时传 app，async with 自动启动
    async with RPCClient("test_server", app="tests.test_server") as client:

        # 简单 call
        result = await client.call("healthy")
        print(result)

        # then + BaseModel 自动注入
        async def handle_task(task: TestTask):
            print(f"Task: {task.task_id}")
            return task.task_id

        task_id = await client.call("test_background").then(handle_task)

        # stream
        async with client.stream(task_id) as listener:
            async for msg in listener:
                r = TestTaskMessage.model_validate(msg.result)
                print(f"Progress: {r.message}")
                if r.task_completed:
                    break

        # error 处理
        try:
            await client.call("nonexistent")
        except RPCError as e:
            print(f"预期错误: {e.code}")


if __name__ == "__main__":
    asyncio.run(test_client())
