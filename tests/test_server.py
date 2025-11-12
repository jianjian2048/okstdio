from typing import Callable, List
import inspect
import asyncio
import uuid
import random
import json
from pydantic import BaseModel, Field
from okstdio.server.application import RPCServer, IOWrite
from okstdio.server.router import RPCRouter
from okstdio.general.jsonrpc_model import JSONRPCRequest, JSONRPCResponse
from okstdio.general.errors import *


class BaseItem(BaseModel):
    name: str
    data: dict


class CreateItem(BaseItem):
    password: str


class PublicItem(BaseItem):
    """公共Item"""

    pass


app = RPCServer(server_name="test_server")


@app.add_middleware(label="日志中间件")
async def log_middleware(request: JSONRPCRequest, call_next: Callable):
    """日志中间件

    这个中间件非常厉害,非常非常厉害
    ```python
    print(f"[LOG]: {request}")
    ```
    """
    print(f"[LOG]: {request}")
    # raise RPCError(code=-32600, message="test error")
    res = await call_next(request)
    return res


@app.add_method("index", label="主方法")
async def index() -> str:
    """测试主方法

    这个主方法固定返回 "Hello, World!"

    ```python
    print("Hello, World!")
    ```
    """
    return "Hello, World!"


@app.add_method("item", label="获取实例")
def item(item: CreateItem) -> PublicItem:
    """获取实例方法"""
    return PublicItem(name=item.name, data=item.data)


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


one = RPCRouter(prefix="one", label="第一个路由")


@one.add_method("index")
async def one_index():
    return "Hello, One!"


@one.add_method("api")
async def one_api():
    return "Hello, One API!"


two = RPCRouter(prefix="two")


@two.add_method("index")
async def two_index(name: str):
    print(f"two_index: {name}")
    return f"Hello, {name}"


@two.add_method("api")
async def two_api():
    return "Hello, Two API!"


one.include_router(two)
app.include_router(one)


async def main():
    try:
        test = await app.handle_request(
            '{"jsonrpc": "2.0", "method": "one.two.index", "params": {"name": "jianjian"}, "id": 10}'
        )
        print(test.model_dump_json())
    except RPCError as e:
        print(e)


if __name__ == "__main__":
    with open("doc.md", "w", encoding="utf-8") as f:
        f.write(app.docs_markdown())

    with open("doc.json", "w", encoding="utf-8") as f:
        json.dump(app.docs_json(), f, ensure_ascii=False, indent=4)
