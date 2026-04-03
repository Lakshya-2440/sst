from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ConfigDict
from pydantic import BaseModel as PydanticBaseModel

from app import __version__
from app.env import SQLAgentEnv
from app.models import ActionModel
from app.tasks import TASKS


class ResetRequest(PydanticBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    task_id: str | None = None


app = FastAPI(title="sql-agent-env", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = SQLAgentEnv()


def _serialize_task(task) -> dict[str, Any]:
    return task.model_dump(exclude={"expected_query"})


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "env": "sql-agent-env", "version": __version__}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/reset")
def reset(payload: ResetRequest = Body(default=ResetRequest())):
    try:
        return env.reset(task_id=payload.task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/step")
def step(action: ActionModel):
    try:
        return env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state")
def state():
    return env.state()


@app.get("/tasks")
def tasks() -> list[dict[str, Any]]:
    return [_serialize_task(task) for task in TASKS]
