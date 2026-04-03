from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AppBaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class TaskDefinition(AppBaseModel):
    id: str
    name: str
    description: str
    difficulty: TaskDifficulty
    schema_context: str
    question: str
    expected_query: str = Field(..., exclude=True, repr=False)
    max_score: float


class ObservationModel(AppBaseModel):
    task_id: str
    schema_context: str
    question: str
    last_query: str | None = None
    last_result: list[dict[str, Any]] | None = None
    last_error: str | None = None
    step_count: int = 0
    done: bool = False
    reward_so_far: float = 0.0


class ActionModel(AppBaseModel):
    query: str


class StepResult(AppBaseModel):
    observation: ObservationModel
    reward: float
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class ResetResult(AppBaseModel):
    observation: ObservationModel
    task_id: str
    message: str


class StateResult(AppBaseModel):
    current_task_id: str | None = None
    step_count: int = 0
    done: bool = False
    reward_so_far: float = 0.0
    observation: ObservationModel | None = None
