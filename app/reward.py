from __future__ import annotations

from typing import Any

from app.graders import SQLGrader
from app.models import ActionModel, TaskDefinition


class RewardComputer:
    def __init__(self, grader: SQLGrader | None = None) -> None:
        self.grader = grader or SQLGrader()

    def compute(
        self,
        task: TaskDefinition,
        action: ActionModel,
        db,
        step_count: int,
    ) -> tuple[float, dict[str, Any]]:
        grader_score = self.grader.grade(task, action, db)
        penalty_multiplier = max(0.0, 1 - (0.05 * step_count))
        final_reward = max(0.0, min(1.0, grader_score * penalty_multiplier))
        breakdown = {
            "grader_score": grader_score,
            "step_penalty_multiplier": penalty_multiplier,
            "final_reward": final_reward,
            "step_count": step_count,
            "grading_details": self.grader.last_details,
        }
        return final_reward, breakdown
