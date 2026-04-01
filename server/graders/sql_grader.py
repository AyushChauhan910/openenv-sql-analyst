import sqlite3
from server.models import Reward


class SQLGrader:
    def grade(
        self,
        sql_query: str,
        expected: list[dict],
        connection: sqlite3.Connection
    ) -> Reward:
        try:
            cursor = connection.execute(sql_query)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            error_msg = str(e)
            if "syntax" in error_msg.lower():
                return Reward(
                    score=0.0,
                    feedback=f"SQL syntax error: {error_msg}",
                    partial_credit={}
                )
            return Reward(
                score=0.1,
                feedback=f"Query failed: {error_msg}",
                partial_credit={}
            )

        actual = [dict(r) for r in rows]

        if not actual:
            return Reward(
                score=0.2,
                feedback="Query returned no rows",
                partial_credit={}
            )

        partial_credit = {}
        expected_columns = set(expected[0].keys()) if expected else set()
        actual_columns = set(actual[0].keys()) if actual else set()

        if expected_columns == actual_columns:
            partial_credit["columns"] = True

        if len(actual) == len(expected):
            partial_credit["row_count"] = True

        column_score = 0.2 if partial_credit.get("columns") else 0.0
        row_count_score = 0.1 if partial_credit.get("row_count") else 0.0

        expected_set = self._normalize_rows(expected, expected_columns)
        actual_set = self._normalize_rows(actual, expected_columns)

        if expected_set == actual_set:
            return Reward(
                score=1.0,
                feedback="Perfect answer!",
                partial_credit=partial_credit
            )

        matched = expected_set & actual_set
        total_cells = len(expected_set) * len(expected_columns) if expected_set else 1
        matched_cells = len(matched) * len(expected_columns) if matched else 0
        value_match_ratio = matched_cells / total_cells if total_cells > 0 else 0

        if value_match_ratio >= 0.8:
            return Reward(
                score=0.8,
                feedback="Close but some values differ",
                partial_credit=partial_credit
            )
        elif value_match_ratio >= 0.5:
            return Reward(
                score=0.6,
                feedback="Partially correct but many values differ",
                partial_credit=partial_credit
            )
        else:
            score = 0.3 + column_score + row_count_score
            return Reward(
                score=round(min(score, 0.59), 2),
                feedback="Query returned results but values do not match expected",
                partial_credit=partial_credit
            )

    def _normalize_rows(
        self,
        rows: list[dict],
        columns: set[str]
    ) -> set[tuple]:
        normalized = set()
        for row in rows:
            values = []
            for col in sorted(columns):
                val = row.get(col)
                if isinstance(val, float):
                    val = round(val, 2)
                values.append(val)
            normalized.add(tuple(values))
        return normalized
