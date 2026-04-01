from server.database.schema import get_db_connection


class EasyTask:
    def __init__(self):
        self._question = (
            "How many orders were placed in 2024, and what is the total revenue? "
            "Return columns: total_orders, total_revenue"
        )
        self._max_steps = 5

    def get_question(self) -> str:
        return self._question

    def get_max_steps(self) -> int:
        return self._max_steps

    def get_expected(self) -> list[dict]:
        conn, _ = get_db_connection()
        rows = conn.execute("""
            SELECT
                COUNT(*) AS total_orders,
                ROUND(SUM(total_amount), 2) AS total_revenue
            FROM orders
            WHERE strftime('%Y', order_date) = '2024'
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
