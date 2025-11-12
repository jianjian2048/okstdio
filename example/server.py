import logging
import asyncio
from logging.handlers import RotatingFileHandler
from typing import Annotated
from pydantic import BaseModel, Field
from okstdio.server import RPCServer, RPCRouter, IOWrite
from okstdio.general.jsonrpc_model import *
from okstdio.general.errors import *
from .databases import app_db
from .schemas import *


# 设置日志
FORMAT = "[%(asctime)s] %(levelname)s @%(name)s > %(message)s"
DATEFMT = "%m-%d %H:%M:%S"
LOG_HANDLER = RotatingFileHandler(
    filename="example/assets/app.log",
    maxBytes=2 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
)
logging.basicConfig(
    format=FORMAT,
    datefmt=DATEFMT,
    level=logging.INFO,
    handlers=[LOG_HANDLER],
)
logger = logging.getLogger("server")

# 创建 APP
app = RPCServer("example_server", label="示例服务器")


@app.add_middleware(label="请求日志")
async def logmw(request: JSONRPCRequest, call_next):
    logger.info(f"收到请求: {request.model_dump_json()}")
    res = await call_next(request)
    return res


@app.add_method(name="healthy", label="健康")
def healthy() -> dict:
    """返回服务器是否健康

    return :
    ```json
    {"status": "ok"}
    ```
    """
    return {"status": "ok"}


hero_router = RPCRouter(prefix="hero", label="英雄方法")


@hero_router.add_method(name="create")
def create(hero: CreateHero) -> PublicHero | JSONRPCServerErrorDetail:
    """创建一个英雄:
    ```json
    {"jsonrpc": "2.0", "method": "hero.create", "params": {"hero": {"hero_name": "英雄名称"}}, "id": 1}
    ```
    """
    db_hero = app_db.get_hero(hero.hero_name)
    if db_hero:
        return JSONRPCServerErrorDetail(
            -32001, message=f"英雄 {hero.hero_name} 已经存在,无法再次创建."
        )
    return hero.create_hero()


async def fighting(fighting_task: FightingTask, io_write: IOWrite):
    monster = ["史莱姆", "哥布林", "牛头"]
    while True:
        ...


tasks = {}


@hero_router.add_method(name="dungeon")
async def dungeon(
    hero_name: Annotated[str, Field(..., description="英雄名称")], io_write: IOWrite
) -> FightingTask | JSONRPCServerErrorDetail:
    """进入一个副本, 打怪升级:
    ```json
    {"jsonrpc": "2.0", "method": "hero.dungeon", "params": {"hero_name": "英雄名称"}, "id": 1}
    ```
    """
    hero = app_db.get_hero(hero_name)
    if not hero:
        return JSONRPCServerErrorDetail(
            -32002, message=f"英雄 {hero.hero_name} 不存在."
        )
    hero = PublicHero(hero_id=hero[0], hero_name=hero[1], level=hero[2])
    fighting_task = FightingTask(hero=hero)
    task = asyncio.create_task(fighting(fighting_task, io_write))
    tasks[fighting_task.task_id] = task
    return fighting_task


app.include_router(hero_router)

if __name__ == "__main__":
    app.docs_markdown()
    app.runserver()
    app_db.close()
