from __future__ import annotations

import random
import sqlite3

from app.database import clone_connection, execute_query, get_connection
from app.models import ActionModel, ObservationModel, ResetResult, StateResult, StepResult
from app.reward import RewardComputer
from app.tasks import TASKS, TASKS_BY_ID


class SQLAgentEnv:
    def __init__(self) -> None:
        self.reward_computer = RewardComputer()
        self.connection: sqlite3.Connection | None = None
        self.current_task = None
        self._state: ObservationModel | None = None

    @property
    def state_snapshot(self) -> ObservationModel | None:
        return self._state

    def reset(self, task_id: str | None = None) -> ResetResult:
        if task_id is None:
            task = random.choice(TASKS)
        else:
            if task_id not in TASKS_BY_ID:
                raise ValueError(f"Unknown task_id: {task_id}")
            task = TASKS_BY_ID[task_id]

        if self.connection is not None:
            self.connection.close()

        self.connection = get_connection()
        self.current_task = task
        self._state = ObservationModel(
            task_id=task.id,
            schema_context=task.schema_context,
            question=task.question,
            last_query=None,
            last_result=None,
            last_error=None,
            step_count=0,
            done=False,
            reward_so_far=0.0,
        )
        return ResetResult(
            observation=self._state,
            task_id=task.id,
            message=f"Environment reset for task '{task.id}'.",
        )

    def step(self, action: ActionModel) -> StepResult:
        if self.connection is None or self.current_task is None or self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() before step().")

        next_step_count = self._state.step_count + 1
        evaluation_connection = clone_connection(self.connection)
        try:
            rows, _, error = execute_query(action.query, evaluation_connection)
        finally:
            evaluation_connection.close()

        reward, breakdown = self.reward_computer.compute(
            self.current_task,
            action,
            self.connection,
            next_step_count,
        )
        done = reward >= 0.9 or next_step_count >= 10

        self._state = ObservationModel(
            task_id=self.current_task.id,
            schema_context=self.current_task.schema_context,
            question=self.current_task.question,
            last_query=action.query,
            last_result=rows if error is None else None,
            last_error=error,
            step_count=next_step_count,
            done=done,
            reward_so_far=max(self._state.reward_so_far, reward),
        )
        return StepResult(
            observation=self._state,
            reward=reward,
            done=done,
            info=breakdown,
        )

    def state(self) -> StateResult:
        if self._state is None:
            return StateResult(
                current_task_id=None,
                step_count=0,
                done=False,
                reward_so_far=0.0,
                observation=None,
            )

        return StateResult(
            current_task_id=self.current_task.id if self.current_task is not None else None,
            step_count=self._state.step_count,
            done=self._state.done,
            reward_so_far=self._state.reward_so_far,
            observation=self._state,
        )
