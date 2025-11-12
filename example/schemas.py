"""数据模型定义

这个模块定义了所有的 Pydantic 数据模型，用于：
- API 请求/响应的类型验证
- 自动生成 API 文档
- 序列化/反序列化
"""

from __future__ import annotations
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, Field


class HealthyResult(BaseModel):
    """健康检查响应模型
    
    用于 healthy 接口的返回值
    """

    status: Literal["ok"] = Field("ok", description="健康状态常量")


class BaseHero(BaseModel):
    """英雄基类
    
    包含所有英雄共有的字段
    """

    hero_name: str = Field(description="英雄名称")


class PublicHero(BaseHero):
    """公开的英雄信息
    
    用于返回给客户端的英雄数据
    不包含敏感信息
    """

    hero_id: int | None = Field(None, description="英雄ID")
    level: int = Field(..., ge=0, le=50, description="等级 0-50")


class CreateHero(BaseHero):
    """创建英雄的请求参数
    
    只需要提供英雄名称
    其他字段（ID、等级）由服务器自动生成
    """

    pass


class FightingTask(BaseModel):
    """战斗任务信息
    
    当英雄进入副本时返回的任务对象
    包含任务ID（用于后续监听战斗结果）和英雄信息
    """

    task_id: str = Field(default_factory=lambda: uuid4().hex, description="任务ID")
    hero: PublicHero = Field(..., description="英雄")


class FightingResult(BaseModel):
    """战斗结果
    
    每次战斗完成后推送给客户端的消息
    """

    fighting_news: str = Field(..., description="战斗信息")
    rewards: str = Field(..., description="战利品")
