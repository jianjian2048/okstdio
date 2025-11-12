from __future__ import annotations
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, Field
from .databases import app_db


class HealthyResult(BaseModel):
    """健康响应"""

    status: Literal["ok"] = Field("ok", description="健康状态常量")


class BaseHero(BaseModel):
    hero_name: str = Field(description="英雄名称")


class PublicHero(BaseHero):
    hero_id: int | None = Field(None, description="英雄ID")
    level: int = Field(..., ge=0, le=50, description="等级 0-50")


class CreateHero(BaseHero):

    def create_hero(self) -> PublicHero:
        app_db.create_hero(self.hero_name)
        hero = app_db.get_hero(self.hero_name)
        return PublicHero(hero_id=hero[0], hero_name=hero[1], level=hero[2])


class FightingTask(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid4().hex, description="任务ID")
    hero: PublicHero = Field(..., description="英雄")
