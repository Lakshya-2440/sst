# SQL Agent Environment

## Overview

This environment simulates a real-world text-to-SQL workflow used in analytics teams, internal data tooling, and enterprise reporting systems. An agent receives a database schema plus a natural language request, writes a SQLite query, and is scored on execution quality and answer correctness. The environment is designed for iterative agent evaluation, partial-credit grading, and reproducible benchmarking.

## Environment Description

The environment exposes a FastAPI service that serves SQL tasks with increasing difficulty. Each episode starts with a fresh in-memory SQLite database seeded with realistic organizational data across employees, departments, projects, and project assignments. Agents interact through `/reset`, `/step`, `/state`, and `/tasks`.

Key properties:

- Fresh database state on every reset so episodes are independent.
- Deterministic tasks with clear expected SQL behavior.
- Snapshot-safe grading by executing expected and submitted queries on the same DB state.
- Partial-credit rewards to support iterative learning and debugging.

## Observation Space

| Field | Type | Description |
| --- | --- | --- |
| `task_id` | `string` | Active task identifier. |
| `schema_context` | `string` | Full schema and relationship context provided to the agent. |
| `question` | `string` | Natural language prompt the agent must answer. |
| `last_query` | `string \| null` | Most recent SQL query submitted by the agent. |
| `last_result` | `array \| null` | JSON-serializable result rows from the previous query. |
| `last_error` | `string \| null` | SQL execution error from the previous query, if any. |
| `step_count` | `integer` | Number of attempts taken in the current episode. |
| `done` | `boolean` | Whether the episode has terminated. |
| `reward_so_far` | `number` | Best reward achieved so far in the episode. |

## Action Space

The action space is a single field:

- `query` (`string`): a single SQLite SQL query produced by the agent.

## Tasks

| id | difficulty | description | max_score |
| --- | --- | --- | --- |
| `task_easy` | `easy` | List Engineering employees and salaries ordered by salary descending. | `1.0` |
| `task_medium` | `medium` | Compute department average salaries and keep departments above 70000. | `1.0` |
| `task_hard` | `hard` | Aggregate direct-report project hours for managers with more than one report. | `1.0` |

## Reward Function

The environment uses partial credit based on the submitted query result compared with the expected query result:

- `0.0`: query fails with syntax or execution error.
- `0.2`: query runs but returns zero rows when rows are expected.
- `0.4`: query returns the correct columns but wrong data.
- `0.6`: query returns the correct columns and correct row count.
- `0.8`: query returns the correct data but differs in ordering or numeric rounding.
- `1.0`: query output exactly matches the expected output.

The step-level reward is then adjusted with a step penalty:

```text
final_reward = grader_score * (1 - 0.05 * step_count)
```

The result is clamped into `[0.0, 1.0]`.

## Setup & Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

Start the API directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Or use Docker:

```bash
docker build -t sql-agent-env .
docker run --rm -p 7860:7860 sql-agent-env
```

Validate the environment:

```bash
python validate.py
```

## Deploy to HF Spaces

1. Create a new Hugging Face Space.
2. Select **Docker** as the Space SDK.
3. Name the Space and create it.
4. Upload all repository files, or push the repo to the Space Git remote.
5. In the Space settings, set the app port to `7860` if needed.
6. Add secrets for `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` if you want to run `inference.py` inside the Space or from the Space terminal.
7. Wait for the Docker build to complete.
8. Open the Space URL and verify `/health`, `/tasks`, `/reset`, and `/state`.

## Running Inference

The inference runner executes all three tasks sequentially and prints strict JSON logs to stdout.

Example:

```bash
export OPENENV_API_BASE=http://localhost:7860
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
export HF_TOKEN=your_token_here
python inference.py
```

If the LLM endpoint is not configured, `inference.py` falls back to deterministic baseline SQL so the environment remains runnable locally.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `OPENENV_API_BASE` | No | Base URL for the environment API. Defaults to `http://localhost:7860`. |
| `API_BASE_URL` | For LLM inference | OpenAI-compatible model endpoint used by `inference.py`. |
| `MODEL_NAME` | For LLM inference | Model identifier passed to the OpenAI client. |
| `HF_TOKEN` | For LLM inference | API token used as the OpenAI-compatible client key. |

## API Reference

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Environment metadata and version. |
| `GET` | `/health` | Liveness check. |
| `POST` | `/reset` | Starts a fresh episode for a specific task or a random task. |
| `POST` | `/step` | Submits an SQL query and receives graded feedback. |
| `GET` | `/state` | Returns the current environment state snapshot. |
| `GET` | `/tasks` | Lists the three public task definitions without expected SQL. |

### Request and Response Notes

- `POST /reset` accepts `{"task_id": "task_easy"}` or an empty JSON object.
- `POST /step` accepts `{"query": "SELECT ...;"}`.
- `GET /tasks` omits internal grader-only SQL.
- `done` becomes `true` when the reward is at least `0.9` or the step count reaches `10`.

## Baseline Scores

Approximate expected rewards for a strong baseline that solves each task on the first attempt:

| Task | Approximate score |
| --- | --- |
| `task_easy` | `0.95` |
| `task_medium` | `0.95` |
| `task_hard` | `0.95` |

These scores reflect the built-in first-step penalty multiplier of `0.95`.
