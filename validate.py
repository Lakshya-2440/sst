from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
BASE_URL = "http://localhost:7860"


def print_result(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {name}{suffix}")
    return passed


def check_openenv_yaml() -> bool:
    config_path = ROOT / "openenv.yaml"
    if not config_path.exists():
        return print_result("openenv.yaml exists and has required fields", False, "file missing")

    content = config_path.read_text(encoding="utf-8")
    required_snippets = [
        "name: sql-agent-env",
        'version: "1.0.0"',
        "description:",
        "tasks:",
        "observation_space:",
        "action_space:",
        'api_base: "http://localhost:7860"',
        "endpoints:",
        "reset: POST /reset",
        "step: POST /step",
        "state: GET /state",
        "tasks: GET /tasks",
        "id: task_easy",
        "id: task_medium",
        "id: task_hard",
    ]
    missing = [snippet for snippet in required_snippets if snippet not in content]
    return print_result(
        "openenv.yaml exists and has required fields",
        not missing,
        "missing fields" if missing else "",
    )


def ensure_server() -> subprocess.Popen | None:
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return None
    except requests.RequestException:
        pass

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "7860",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                return process
        except requests.RequestException:
            time.sleep(0.5)

    process.terminate()
    process.wait(timeout=5)
    raise RuntimeError("Unable to start FastAPI server for validation.")


def main() -> int:
    results: list[bool] = []
    results.append(check_openenv_yaml())

    server_process = None
    try:
        server_process = ensure_server()

        try:
            root_response = requests.get(f"{BASE_URL}/", timeout=5)
            ok = root_response.status_code == 200
            results.append(print_result("GET / returns 200", ok, f"status={root_response.status_code}"))
        except requests.RequestException as exc:
            results.append(print_result("GET / returns 200", False, str(exc)))

        try:
            reset_response = requests.post(
                f"{BASE_URL}/reset",
                json={"task_id": "task_easy"},
                timeout=5,
            )
            reset_ok = reset_response.status_code == 200 and "observation" in reset_response.json()
            results.append(print_result("POST /reset works and returns observation", reset_ok))
        except requests.RequestException as exc:
            results.append(print_result("POST /reset works and returns observation", False, str(exc)))

        try:
            step_response = requests.post(
                f"{BASE_URL}/step",
                json={
                    "query": (
                        "SELECT e.name, e.salary "
                        "FROM employees AS e "
                        "JOIN departments AS d ON e.department_id = d.id "
                        "WHERE d.name = 'Engineering' "
                        "ORDER BY e.salary DESC, e.name ASC;"
                    )
                },
                timeout=5,
            )
            payload = step_response.json()
            reward = payload.get("reward")
            step_ok = step_response.status_code == 200 and isinstance(reward, (float, int)) and 0 <= reward <= 1
            results.append(print_result("POST /step works and returns reward in [0,1]", step_ok))
        except requests.RequestException as exc:
            results.append(print_result("POST /step works and returns reward in [0,1]", False, str(exc)))

        try:
            state_response = requests.get(f"{BASE_URL}/state", timeout=5)
            state_ok = state_response.status_code == 200 and "step_count" in state_response.json()
            results.append(print_result("GET /state works", state_ok))
        except requests.RequestException as exc:
            results.append(print_result("GET /state works", False, str(exc)))

        try:
            tasks_response = requests.get(f"{BASE_URL}/tasks", timeout=5)
            tasks_payload = tasks_response.json()
            tasks_ok = tasks_response.status_code == 200 and isinstance(tasks_payload, list) and len(tasks_payload) >= 3
            results.append(print_result("GET /tasks returns 3+ tasks", tasks_ok))
        except requests.RequestException as exc:
            results.append(print_result("GET /tasks returns 3+ tasks", False, str(exc)))
    except Exception as exc:
        results.append(print_result("FastAPI server startup", False, str(exc)))
    finally:
        if server_process is not None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    results.append(
        print_result(
            "inference.py exists at root",
            (ROOT / "inference.py").exists(),
        )
    )
    results.append(
        print_result(
            "Dockerfile exists",
            (ROOT / "Dockerfile").exists(),
        )
    )

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
