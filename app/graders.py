from __future__ import annotations

from collections import Counter
from typing import Any

from app.database import clone_connection, execute_query
from app.models import ActionModel, TaskDefinition


class SQLGrader:
    def __init__(self) -> None:
        self.last_details: dict[str, Any] = {}

    def _normalize_columns(self, columns: list[str]) -> list[str]:
        return [column.lower() for column in columns]

    def _normalize_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            normalized_rows.append({str(key).lower(): value for key, value in row.items()})
        return normalized_rows

    def _normalize_value(self, value: Any, rounding_digits: int | None = None) -> Any:
        if isinstance(value, float):
            return round(value, rounding_digits if rounding_digits is not None else 10)
        if isinstance(value, str):
            return value.strip()
        return value

    def _canonicalize_rows(
        self,
        rows: list[dict[str, Any]],
        columns: list[str],
        rounding_digits: int | None = None,
    ) -> list[tuple[Any, ...]]:
        canonical_rows: list[tuple[Any, ...]] = []
        for row in rows:
            canonical_row = tuple(
                self._normalize_value(row.get(column), rounding_digits=rounding_digits)
                for column in columns
            )
            canonical_rows.append(canonical_row)
        return canonical_rows

    def grade(self, task: TaskDefinition, action: ActionModel, db) -> float:
        """
        Returns reward between 0.0 and 1.0 with PARTIAL CREDIT:
        - 0.0  -> query has syntax error or crashes
        - 0.2  -> query runs but returns 0 rows when rows expected
        - 0.4  -> query returns correct columns but wrong data
        - 0.6  -> query returns correct row count and columns
        - 0.8  -> query returns correct data but wrong ordering/rounding
        - 1.0  -> query output exactly matches expected output
        Compare by executing both the agent's query and expected query on the same DB
        and comparing result sets. Normalize column names to lowercase for comparison.
        """

        actual_connection = clone_connection(db)
        expected_connection = clone_connection(db)
        try:
            actual_rows, actual_columns, actual_error = execute_query(action.query, actual_connection)
            expected_rows, expected_columns, expected_error = execute_query(
                task.expected_query,
                expected_connection,
            )
        finally:
            actual_connection.close()
            expected_connection.close()

        self.last_details = {
            "actual_error": actual_error,
            "expected_error": expected_error,
            "actual_row_count": len(actual_rows),
            "expected_row_count": len(expected_rows),
            "actual_columns": actual_columns,
            "expected_columns": expected_columns,
            "match_level": "none",
        }

        if actual_error or expected_error:
            self.last_details["match_level"] = "error"
            return 0.0

        normalized_actual_columns = self._normalize_columns(actual_columns)
        normalized_expected_columns = self._normalize_columns(expected_columns)
        normalized_actual_rows = self._normalize_rows(actual_rows)
        normalized_expected_rows = self._normalize_rows(expected_rows)

        if expected_rows and not actual_rows:
            self.last_details["match_level"] = "empty_result"
            return 0.2

        columns_match = normalized_actual_columns == normalized_expected_columns
        if not columns_match:
            self.last_details["match_level"] = "wrong_columns"
            return 0.0

        actual_exact = self._canonicalize_rows(
            normalized_actual_rows,
            normalized_actual_columns,
            rounding_digits=None,
        )
        expected_exact = self._canonicalize_rows(
            normalized_expected_rows,
            normalized_expected_columns,
            rounding_digits=None,
        )
        if actual_exact == expected_exact:
            self.last_details["match_level"] = "exact"
            return 1.0

        actual_loose = Counter(
            self._canonicalize_rows(
                normalized_actual_rows,
                normalized_actual_columns,
                rounding_digits=2,
            )
        )
        expected_loose = Counter(
            self._canonicalize_rows(
                normalized_expected_rows,
                normalized_expected_columns,
                rounding_digits=2,
            )
        )
        if actual_loose == expected_loose:
            self.last_details["match_level"] = "correct_data_wrong_order_or_rounding"
            return 0.8

        if len(normalized_actual_rows) == len(normalized_expected_rows):
            self.last_details["match_level"] = "correct_columns_and_row_count"
            return 0.6

        self.last_details["match_level"] = "correct_columns_wrong_data"
        return 0.4
