from __future__ import annotations
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, Field


class HealthyResult(BaseModel):
    """健康响应"""

    status: Literal["ok"] = Field("ok", description="健康状态常量")


class BaseHero(BaseModel):
    hero_name: str = Field(description="英雄名称")


class PublicHero(BaseHero):
    """英雄"""

    hero_id: int | None = Field(None, description="英雄ID")
    level: int = Field(..., ge=0, le=50, description="等级 0-50")


class CreateHero(BaseHero):
    """创建英雄"""

    pass


class FightingTask(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid4().hex, description="任务ID")
    hero: PublicHero = Field(..., description="英雄")


class FightingResult(BaseModel):
    fighting_news: str = Field(..., description="战斗信息")
    rewards: str = Field(..., description="战利品")
