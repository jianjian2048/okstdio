from typing import Callable, List
from pydantic import BaseModel, Field
import asyncio
import uuid
import random
from okstdio.server.application import RPCServer, IOWrite
from okstdio.server.router import RPCRouter
from okstdio.general.jsonrpc_model import JSONRPCRequest, JSONRPCResponse
from okstdio.general.errors import *


app = RPCServer()


@app.add_middleware()
async def log_middleware(request: JSONRPCRequest, call_next: Callable):
    print(f"app 前处理: {request}")
    # raise RPCError(code=-32600, message="test error")
    res = await call_next(request)
    print(f"app 后处理: {request}")
    return res


class Hero(BaseModel):
    name: str = Field(description="英雄名称")
    skills: List[str] = Field(description="技能列表")


tasks = {}


async def fighting(task_id: str, hero: Hero, io_write: IOWrite):
    while True:
        action = f"英雄: {hero.name}, 释放技能: {random.choice(hero.skills)}"
        response = JSONRPCResponse(id=task_id, result=action)
        await io_write.write(response)
        await asyncio.sleep(2)


@app.add_method("backend")
async def backend(hero: Hero, io_write: IOWrite):
    """简单后台任务"""

    task_id = uuid.uuid4().hex
    task = asyncio.create_task(fighting(task_id, hero, io_write))
    tasks[task_id] = task
    return task_id


async def main():
    try:
        test = await app.handle_request(
            '{"jsonrpc": "2.0","id": 1,"method": "backend","params": {"hero": {"name": "jianjian","skills": ["skill1", "skill2", "skill3"] } } }'
        )
        print(test.model_dump_json())
        print(tasks)
        await asyncio.sleep(10)

    except RPCError as e:
        print(e)
        print(e.data)


if __name__ == "__main__":
    # import asyncio

    # asyncio.run(main())

    print(Hero.model_json_schema())
