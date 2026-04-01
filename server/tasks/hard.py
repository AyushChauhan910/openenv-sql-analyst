from server.database.schema import get_db_connection


class HardTask:
    def __init__(self):
        self._question = (
            "For each product category, calculate the best selling month (by revenue) "
            "and the revenue in that month. Use a CTE or window function. "
            "Return columns: category, best_month (YYYY-MM), monthly_revenue"
        )
        self._max_steps = 10

    def get_question(self) -> str:
        return self._question

    def get_max_steps(self) -> int:
        return self._max_steps

    def get_expected(self) -> list[dict]:
        conn, _ = get_db_connection()
        rows = conn.execute("""
            WITH monthly_category_revenue AS (
                SELECT
                    p.category,
                    strftime('%Y-%m', o.order_date) AS month,
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.category, month
            ),
            ranked AS (
                SELECT
                    category,
                    month AS best_month,
                    monthly_revenue,
                    ROW_NUMBER() OVER (
                        PARTITION BY category
                        ORDER BY monthly_revenue DESC
                    ) AS rn
                FROM monthly_category_revenue
            )
            SELECT category, best_month, monthly_revenue
            FROM ranked
            WHERE rn = 1
            ORDER BY category
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
