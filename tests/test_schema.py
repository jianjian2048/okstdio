from __future__ import annotations
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, Field


class TestTask(BaseModel):

    task_id: str = Field(default_factory=lambda: uuid4().hex, description="任务ID")


class TestTaskMessage(BaseModel):

    message: str = Field(..., description="任务信息")
    task_completed: bool = Field(False, description="任务是否已完成")
