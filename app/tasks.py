from __future__ import annotations

from app.models import TaskDefinition, TaskDifficulty


SCHEMA_CONTEXT = """Tables:
1. employees(
   id INTEGER PRIMARY KEY,
   name TEXT,
   department_id INTEGER REFERENCES departments(id),
   salary INTEGER,
   hire_date TEXT,
   manager_id INTEGER REFERENCES employees(id)
)
2. departments(
   id INTEGER PRIMARY KEY,
   name TEXT,
   budget INTEGER,
   location TEXT
)
3. projects(
   id INTEGER PRIMARY KEY,
   name TEXT,
   department_id INTEGER REFERENCES departments(id),
   start_date TEXT,
   end_date TEXT,
   status TEXT
)
4. project_assignments(
   employee_id INTEGER REFERENCES employees(id),
   project_id INTEGER REFERENCES projects(id),
   role TEXT,
   hours_worked INTEGER,
   PRIMARY KEY (employee_id, project_id)
)

Relationships:
- employees.department_id joins departments.id
- projects.department_id joins departments.id
- project_assignments.employee_id joins employees.id
- project_assignments.project_id joins projects.id
- employees.manager_id is a self-reference to employees.id for manager-report relationships
"""


TASKS = [
    TaskDefinition(
        id="task_easy",
        name="Engineering Salaries",
        description=(
            "Retrieve employees in the Engineering department with their salaries "
            "sorted from highest salary to lowest."
        ),
        difficulty=TaskDifficulty.easy,
        schema_context=SCHEMA_CONTEXT,
        question=(
            "List the names and salaries of all employees in the 'Engineering' department, "
            "ordered by salary descending."
        ),
        expected_query="""
        SELECT e.name, e.salary
        FROM employees AS e
        JOIN departments AS d ON e.department_id = d.id
        WHERE d.name = 'Engineering'
        ORDER BY e.salary DESC, e.name ASC;
        """.strip(),
        max_score=1.0,
    ),
    TaskDefinition(
        id="task_medium",
        name="Department Salary Averages",
        description=(
            "Compute average salary by department and keep only departments whose "
            "average salary is above 70000."
        ),
        difficulty=TaskDifficulty.medium,
        schema_context=SCHEMA_CONTEXT,
        question=(
            "Find the average salary per department and return only departments "
            "where the average salary exceeds 70000. Include department name and "
            "average salary rounded to 2 decimal places."
        ),
        expected_query="""
        SELECT
            d.name AS department_name,
            ROUND(AVG(e.salary), 2) AS average_salary
        FROM departments AS d
        JOIN employees AS e ON e.department_id = d.id
        GROUP BY d.id, d.name
        HAVING AVG(e.salary) > 70000
        ORDER BY average_salary DESC, department_name ASC;
        """.strip(),
        max_score=1.0,
    ),
    TaskDefinition(
        id="task_hard",
        name="Manager Team Utilization",
        description=(
            "Aggregate direct-report project hours for each manager and include only "
            "managers with more than one direct report."
        ),
        difficulty=TaskDifficulty.hard,
        schema_context=SCHEMA_CONTEXT,
        question=(
            "For each manager, find the total hours worked by all employees they manage "
            "across all projects. Return manager name, number of direct reports, "
            "and total hours. Only include managers with more than 1 direct report."
        ),
        expected_query="""
        WITH manager_rollup AS (
            SELECT
                m.id AS manager_id,
                m.name AS manager_name,
                COUNT(DISTINCT e.id) AS direct_reports,
                COALESCE(SUM(pa.hours_worked), 0) AS total_hours
            FROM employees AS m
            JOIN employees AS e ON e.manager_id = m.id
            LEFT JOIN project_assignments AS pa ON pa.employee_id = e.id
            GROUP BY m.id, m.name
        )
        SELECT manager_name, direct_reports, total_hours
        FROM manager_rollup
        WHERE direct_reports > 1
        ORDER BY total_hours DESC, manager_name ASC;
        """.strip(),
        max_score=1.0,
    ),
]

TASKS_BY_ID = {task.id: task for task in TASKS}
