from __future__ import annotations

import sqlite3
from typing import Any


DEPARTMENTS = [
    (1, "Engineering", 2_500_000, "San Francisco"),
    (2, "Data Science", 1_800_000, "New York"),
    (3, "Finance", 1_200_000, "Chicago"),
    (4, "Human Resources", 900_000, "Austin"),
    (5, "Operations", 1_100_000, "Denver"),
    (6, "Marketing", 1_000_000, "Los Angeles"),
    (7, "Sales", 1_600_000, "Boston"),
    (8, "Legal", 950_000, "Washington DC"),
    (9, "IT Support", 700_000, "Phoenix"),
    (10, "Product", 1_700_000, "Seattle"),
    (11, "Customer Success", 850_000, "Atlanta"),
    (12, "Procurement", 620_000, "Dallas"),
    (13, "Research", 1_400_000, "San Diego"),
    (14, "Security", 1_300_000, "Seattle"),
    (15, "Quality Assurance", 780_000, "Portland"),
    (16, "Design", 980_000, "Brooklyn"),
    (17, "Corporate Strategy", 1_250_000, "San Francisco"),
    (18, "Facilities", 540_000, "Austin"),
    (19, "Compliance", 880_000, "New York"),
    (20, "Administration", 650_000, "San Francisco"),
]

EMPLOYEES = [
    (1, "Alice Carter", 20, 210000, "2014-01-06", None),
    (2, "Brian Kim", 1, 165000, "2015-03-16", 1),
    (3, "Clara Singh", 2, 158000, "2016-06-01", 1),
    (4, "Daniel Brooks", 3, 150000, "2013-09-12", 1),
    (5, "Elena Rossi", 4, 142000, "2017-02-20", 1),
    (6, "Farah Khan", 1, 132000, "2018-04-09", 2),
    (7, "George Miller", 1, 129000, "2018-08-27", 2),
    (8, "Hannah Lee", 1, 98000, "2019-11-04", 6),
    (9, "Ian Moore", 1, 93000, "2020-01-13", 6),
    (10, "Julia Chen", 1, 96000, "2019-07-22", 7),
    (11, "Kevin Patel", 1, 99000, "2021-05-10", 7),
    (12, "Laura Garcia", 2, 136000, "2018-03-05", 3),
    (13, "Michael Brown", 2, 88000, "2020-02-17", 12),
    (14, "Nina Wilson", 2, 121000, "2021-09-06", 12),
    (15, "Omar Ali", 3, 128000, "2017-10-02", 4),
    (16, "Priya Desai", 3, 84000, "2022-01-24", 15),
    (17, "Quentin Hall", 3, 79000, "2021-12-13", 15),
    (18, "Rachel Green", 4, 118000, "2019-03-18", 5),
    (19, "Sam Taylor", 4, 76000, "2022-06-30", 18),
    (20, "Tina Nguyen", 4, 72000, "2023-01-09", 18),
]

PROJECTS = [
    (1, "Platform Modernization", 1, "2025-01-10", "2025-11-30", "active"),
    (2, "Developer Portal", 1, "2025-02-15", "2025-08-31", "active"),
    (3, "API Reliability", 1, "2025-03-01", "2025-12-15", "planning"),
    (4, "Mobile Revamp", 1, "2024-05-12", "2025-04-30", "completed"),
    (5, "Revenue Forecasting", 2, "2025-01-20", "2025-10-30", "active"),
    (6, "Customer Churn Model", 2, "2025-02-05", "2025-09-15", "active"),
    (7, "Feature Store Launch", 2, "2025-04-14", "2026-01-30", "planning"),
    (8, "Fraud Detection Pilot", 2, "2024-08-01", "2025-03-31", "completed"),
    (9, "Quarterly Planning", 3, "2025-01-03", "2025-06-30", "active"),
    (10, "Expense Automation", 3, "2025-02-12", "2025-11-15", "active"),
    (11, "Audit Readiness", 3, "2024-10-07", "2025-05-20", "completed"),
    (12, "Vendor Payment Migration", 3, "2025-05-01", "2026-02-28", "planning"),
    (13, "Hiring Pipeline Refresh", 4, "2025-01-17", "2025-09-30", "active"),
    (14, "Learning Program Rollout", 4, "2025-03-08", "2025-12-10", "planning"),
    (15, "People Analytics Dashboard", 4, "2025-01-25", "2025-10-15", "active"),
    (16, "Benefits Renewal 2026", 4, "2024-09-05", "2025-02-28", "completed"),
    (17, "Security Hardening", 14, "2025-01-11", "2025-12-31", "active"),
    (18, "Brand Refresh", 6, "2025-02-22", "2025-09-20", "planning"),
    (19, "CRM Optimization", 7, "2025-01-29", "2025-08-31", "active"),
    (20, "HQ Renovation", 18, "2024-07-15", "2025-06-15", "completed"),
]

PROJECT_ASSIGNMENTS = [
    (1, 17, "Executive Sponsor", 40),
    (2, 1, "Program Lead", 160),
    (3, 5, "Analytics Sponsor", 155),
    (4, 9, "Budget Owner", 150),
    (5, 13, "People Lead", 148),
    (6, 2, "Engineering Manager", 170),
    (7, 3, "Reliability Lead", 168),
    (8, 1, "Senior Engineer", 182),
    (9, 2, "Backend Engineer", 176),
    (10, 4, "Frontend Engineer", 164),
    (11, 3, "DevOps Engineer", 171),
    (12, 6, "Data Science Manager", 166),
    (13, 5, "Data Analyst", 158),
    (14, 7, "ML Engineer", 162),
    (15, 10, "Finance Manager", 157),
    (16, 10, "Accountant", 149),
    (17, 11, "Financial Analyst", 144),
    (18, 15, "HR Manager", 151),
    (19, 13, "Recruiter", 146),
    (20, 14, "HR Generalist", 139),
]

SCHEMA_SQL = """
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    budget INTEGER NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    salary INTEGER NOT NULL,
    hire_date TEXT NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE project_assignments (
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    hours_worked INTEGER NOT NULL,
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.executescript(SCHEMA_SQL)
    connection.executemany(
        "INSERT INTO departments (id, name, budget, location) VALUES (?, ?, ?, ?);",
        DEPARTMENTS,
    )
    connection.executemany(
        """
        INSERT INTO employees (id, name, department_id, salary, hire_date, manager_id)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        EMPLOYEES,
    )
    connection.executemany(
        """
        INSERT INTO projects (id, name, department_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        PROJECTS,
    )
    connection.executemany(
        """
        INSERT INTO project_assignments (employee_id, project_id, role, hours_worked)
        VALUES (?, ?, ?, ?);
        """,
        PROJECT_ASSIGNMENTS,
    )
    connection.commit()
    return connection


def clone_connection(source_connection: sqlite3.Connection) -> sqlite3.Connection:
    cloned_connection = sqlite3.connect(":memory:")
    cloned_connection.row_factory = sqlite3.Row
    source_connection.backup(cloned_connection)
    cloned_connection.execute("PRAGMA foreign_keys = ON;")
    return cloned_connection


def execute_query(
    sql: str,
    connection: sqlite3.Connection | None = None,
) -> tuple[list[dict[str, Any]], list[str], str | None]:
    owns_connection = connection is None
    active_connection = connection or get_connection()

    try:
        cursor = active_connection.cursor()
        cursor.execute(sql)
        if cursor.description is None:
            return [], [], None

        columns = [description[0] for description in cursor.description]
        fetched_rows = cursor.fetchall()
        rows = [{column: row[column] for column in columns} for row in fetched_rows]
        return rows, columns, None
    except sqlite3.Error as exc:
        return [], [], str(exc)
    finally:
        if owns_connection:
            active_connection.close()
