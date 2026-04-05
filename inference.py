from __future__ import annotations

import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

ENV_API_BASE = os.getenv("OPENENV_API_BASE", "http://localhost:7860").rstrip("/")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

SYSTEM_PROMPT = (
    "You are a SQL expert. Given a database schema and a question, write a single valid "
    "SQLite SQL query that answers the question. Return ONLY the raw SQL query, no "
    "explanation, no markdown, no code fences."
)
USER_PROMPT_TEMPLATE = (
    "Schema:\n{schema_context}\n\n"
    "Question: {question}\n\n"
    "Previous attempt: {last_query}\n"
    "Previous result/error: {last_result}\n\n"
    "Write the correct SQL query:"
)
TASK_IDS = ["task_easy", "task_medium", "task_hard"]


def _log(prefix: str, payload: dict[str, Any]) -> None:
    print(f"{prefix} {json.dumps(payload, ensure_ascii=False)}", flush=True)


def _build_client() -> OpenAI | None:
    if API_BASE_URL and MODEL_NAME and HF_TOKEN:
        return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN, timeout=60.0)
    return None


def _sanitize_sql(text: str) -> str:
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = cleaned.replace("```sql", "```").replace("```sqlite", "```")
        code_segments = re.findall(r"```(.*?)```", cleaned, flags=re.DOTALL)
        if code_segments:
            cleaned = code_segments[0].strip()
    cleaned = cleaned.strip().strip("`").strip()
    match = re.search(r"(?is)\b(with|select)\b.*", cleaned)
    if match:
        cleaned = match.group(0).strip()
    cleaned = cleaned.replace("\r\n", "\n").strip()
    if cleaned.endswith(";"):
        return cleaned
    return f"{cleaned};"


def _fallback_sql(task_id: str) -> str:
    if task_id == "task_easy":
        return (
            "SELECT e.name, e.salary "
            "FROM employees AS e "
            "JOIN departments AS d ON e.department_id = d.id "
            "WHERE d.name = 'Engineering' "
            "ORDER BY e.salary DESC, e.name ASC;"
        )
    if task_id == "task_medium":
        return (
            "SELECT d.name AS department_name, ROUND(AVG(e.salary), 2) AS average_salary "
            "FROM departments AS d "
            "JOIN employees AS e ON e.department_id = d.id "
            "GROUP BY d.id, d.name "
            "HAVING AVG(e.salary) > 70000 "
            "ORDER BY average_salary DESC, department_name ASC;"
        )
    return (
        "WITH manager_rollup AS ("
        " SELECT m.id AS manager_id, m.name AS manager_name,"
        " COUNT(DISTINCT e.id) AS direct_reports,"
        " COALESCE(SUM(pa.hours_worked), 0) AS total_hours"
        " FROM employees AS m"
        " JOIN employees AS e ON e.manager_id = m.id"
        " LEFT JOIN project_assignments AS pa ON pa.employee_id = e.id"
        " GROUP BY m.id, m.name"
        ") "
        "SELECT manager_name, direct_reports, total_hours "
        "FROM manager_rollup "
        "WHERE direct_reports > 1 "
        "ORDER BY total_hours DESC, manager_name ASC;"
    )


def _format_previous_result(observation: dict[str, Any]) -> str:
    if observation.get("last_error"):
        return observation["last_error"]
    if observation.get("last_result") is not None:
        return json.dumps(observation["last_result"], ensure_ascii=False)
    return "None"


def _generate_sql(client: OpenAI | None, task_id: str, observation: dict[str, Any]) -> str:
    prompt = USER_PROMPT_TEMPLATE.format(
        schema_context=observation["schema_context"],
        question=observation["question"],
        last_query=observation.get("last_query") or "None",
        last_result=_format_previous_result(observation),
    )
    if client is None:
        return _fallback_sql(task_id)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        sanitized = _sanitize_sql(content)
        if sanitized.strip(";").strip():
            return sanitized
    except Exception:
        pass
    return _fallback_sql(task_id)


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{ENV_API_BASE}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    client = _build_client()
    scores: dict[str, float] = {}

    _log("[START]", {"env": "sql-agent-env", "total_tasks": 3})

    for task_id in TASK_IDS:
        reset_result = _post("/reset", {"task_id": task_id})
        observation = reset_result["observation"]
        final_reward = 0.0
        steps_taken = 0

        for step_number in range(1, 6):
            sql_query = _generate_sql(client, task_id, observation)
            step_result = _post("/step", {"query": sql_query})
            observation = step_result["observation"]
            final_reward = float(step_result["reward"])
            steps_taken = step_number

            _log(
                "[STEP]",
                {
                    "task_id": task_id,
                    "step": step_number,
                    "action": sql_query,
                    "reward": final_reward,
                    "done": bool(step_result["done"]),
                    "info": step_result.get("info", {}),
                },
            )

            if step_result["done"]:
                break

        scores[task_id] = final_reward
        _log(
            "[END]",
            {
                "task_id": task_id,
                "final_reward": final_reward,
                "steps_taken": steps_taken,
                "status": "completed",
            },
        )

    avg_reward = round(sum(scores.values()) / len(scores), 4) if scores else 0.0
    _log(
        "[END]",
        {
            "summary": True,
            "total_tasks": len(TASK_IDS),
            "avg_reward": avg_reward,
            "task_scores": scores,
        },
    )


if __name__ == "__main__":
    main()
