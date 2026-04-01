from server.database.schema import get_db_connection


class MediumTask:
    def __init__(self):
        self._question = (
            "List the top 5 customers by total amount spent. "
            "Return columns: customer_name, total_spent, order_count, avg_order_value. "
            "Sort by total_spent descending."
        )
        self._max_steps = 8

    def get_question(self) -> str:
        return self._question

    def get_max_steps(self) -> int:
        return self._max_steps

    def get_expected(self) -> list[dict]:
        conn, _ = get_db_connection()
        rows = conn.execute("""
            SELECT
                c.name AS customer_name,
                ROUND(SUM(o.total_amount), 2) AS total_spent,
                COUNT(o.id) AS order_count,
                ROUND(AVG(o.total_amount), 2) AS avg_order_value
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT 5
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
