"""RPC 服务器 - 英雄管理系统

这是一个完整的 JSON-RPC 服务器示例，演示了：
- 基本的 RPC 方法注册
- 路由分组(hero.*)
- 中间件使用(日志记录）
- 流式响应(IOWrite)
- 异步任务管理
- 数据库集成
- 错误处理

运行方式:
    python -m example.server

运行后会:
    1. 生成 API 文档 (example_server.md)
    2. 监听 stdin 等待 JSON-RPC 请求
"""

from ast import Dict

import asyncio
import random
import logging
from logging.handlers import RotatingFileHandler
from typing import Annotated
from pydantic import BaseModel, Field
from okstdio.server import RPCServer, RPCRouter, IOWrite
from okstdio.general.jsonrpc_model import *
from okstdio.general.errors import *
from .databases import app_db
from .schemas import *


# ==================== 日志配置 ====================
# 重要：日志只能写入文件，不能输出到 stdout
# 否则会干扰 JSON-RPC 通信
FORMAT = "[%(asctime)s] %(levelname)s @%(name)s > %(message)s"
DATEFMT = "%m-%d %H:%M:%S"
LOG_HANDLER = RotatingFileHandler(
    filename="example/assets/app.log",
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

logger = logging.getLogger("server")

# ==================== 创建 RPC 服务器 ====================
app = RPCServer("example_server", label="示例服务器")


# ==================== 中间件 ====================
@app.add_middleware(label="请求日志")
async def logmw(request: JSONRPCRequest, call_next):
    """请求日志中间件

    记录所有收到的请求到日志文件
    日志文件路径: /example/assets/app.log
    日志输出格式: [%(asctime)s] %(levelname)s @%(name)s > %(message)s

    Args:
        request: JSON-RPC 请求对象
        call_next: 调用下一个中间件或处理函数
    """
    logger.info(f"收到请求: {request.model_dump_json()}")
    res = await call_next(request)
    return res


# ==================== 顶层方法 ====================
@app.add_method(name="healthy", label="健康")
def healthy() -> HealthyResult:
    """健康检查接口

    用于检查服务器是否正常运行

    Returns:
        HealthyResult: {"status": "ok"}
    """
    return HealthyResult()


# ==================== 英雄路由 ====================
# 将所有英雄相关的方法分组到 hero.* 路由下
hero_router = RPCRouter(prefix="hero", label="英雄方法")


@hero_router.add_method(name="create", label="创建英雄")
def create(hero: CreateHero) -> PublicHero | JSONRPCServerErrorDetail:
    """创建一个英雄

    初始等级为 0，英雄名称必须唯一

    Args:
        hero: 创建英雄的参数(只需要 hero_name）

    Returns:
        PublicHero: 创建成功，返回英雄信息
        JSONRPCServerErrorDetail: 创建失败(名称重复）

    Example:
        请求:
        ```json
        {"jsonrpc": "2.0", "method": "hero.create", "params": {"hero": {"hero_name": "张三"}}, "id": 1}
        ```

        成功响应:
        ```json
        {"jsonrpc": "2.0", "result": {"hero_id": 1, "hero_name": "张三", "level": 0}, "id": 1}
        ```
    """
    db_hero = app_db.get_hero(hero.hero_name)
    if db_hero:
        return JSONRPCServerErrorDetail(
            code=-32001, message=f"英雄 {hero.hero_name} 已经存在,无法再次创建."
        )
    app_db.create_hero(hero.hero_name)
    db_hero = app_db.get_hero(hero.hero_name)
    return PublicHero(hero_id=db_hero[0], hero_name=db_hero[1], level=db_hero[2])


# ==================== 战斗系统 ====================
async def fighting(fighting_task: FightingTask, io_write: IOWrite):
    """战斗主循环

    这是一个后台异步任务，会持续运行直到被取消
    每次战斗后通过 io_write 推送结果给客户端

    Args:
        fighting_task: 战斗任务信息(包含英雄和任务ID）
        io_write: 用于推送消息的写入器

    战斗规则:
        - 随机遇到怪物(史莱姆、哥布林、牛头）
        - 不同怪物战斗时间和经验不同
        - 累积 100 经验自动升级
        - 结果实时推送给客户端
    """
    monsters = ["史莱姆", "哥布林", "牛头"]
    experience = 0
    while True:
        # 随机选择怪物
        increase = 0
        monster = random.choice(monsters)

        # 不同怪物有不同的战斗时间和经验奖励
        if monster == monsters[0]:  # 史莱姆
            fighting_time = random.randint(1, 2)
            increase = 10
        elif monster == monsters[1]:  # 哥布林
            fighting_time = random.randint(2, 3)
            increase = 20
        else:  # 牛头
            fighting_time = random.randint(3, 5)
            increase = 50

        # 模拟战斗时间
        await asyncio.sleep(fighting_time)

        # 累积经验
        experience = experience + increase
        rewards = f"增加了 {increase} 经验"

        # 检查是否升级
        if experience >= 100:
            experience = experience % 100
            level = app_db.hero_upgrade(fighting_task.hero.hero_name)
            fighting_task.hero.level = level
            rewards += f", 升级了! 当前等级 {fighting_task.hero.level}."

        # 推送战斗结果
        response = JSONRPCResponse(
            id=fighting_task.task_id,
            result=FightingResult(
                fighting_news=f"{fighting_task.hero.hero_name} 击败了 {monster}, 耗时 {fighting_time}",
                rewards=rewards,
            ),
        )
        logger.info(f"战斗结果: {fighting_task.hero.hero_name} vs {monster}")
        await io_write.write(response)


# 全局任务字典，用于管理所有战斗任务
# key: task_id, value: asyncio.Task
tasks = {}


@hero_router.add_method(name="dungeon", label="开始战斗")
async def dungeon(
    hero_name: Annotated[
        str, Field(..., description="英雄名称")
    ],  # 简单参数可以使用 Field 添加注释.
    io_write: IOWrite,
) -> FightingTask | JSONRPCServerErrorDetail:
    """进入一个副本, 打怪升级:
    ```json
    {"jsonrpc": "2.0", "method": "hero.dungeon", "params": {"hero_name": "英雄名称"}, "id": 1}
    ```
    """
    hero = app_db.get_hero(hero_name)
    if not hero:
        return JSONRPCServerErrorDetail(
            code=-32002, message=f"英雄 {hero_name} 不存在."
        )
    hero = PublicHero(hero_id=hero[0], hero_name=hero[1], level=hero[2])
    fighting_task = FightingTask(hero=hero)
    task = asyncio.create_task(fighting(fighting_task, io_write))
    tasks[fighting_task.task_id] = task
    logger.info(fighting_task)
    return fighting_task


@hero_router.add_method(name="stop_dungeon", label="停止战斗")
async def stop_dungeon(
    task_id: Annotated[str, Field(..., description="战斗的ID")],
) -> bool:
    """通过战斗的ID停止"""
    task = tasks.get(task_id, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    return True


app.include_router(hero_router)

if __name__ == "__main__":
    app.docs_markdown()
    app.runserver()
    app_db.close()
