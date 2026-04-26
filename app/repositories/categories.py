from typing import List

from psycopg2.extras import RealDictCursor

from app.db import Database
from app.schemas.categories import CategoryCount

_CATEGORIES_SQL = """
    SELECT category, COUNT(*) AS count
    FROM summaries
    WHERE is_safe = true
    GROUP BY category
    ORDER BY count DESC
"""


class CategoryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_counts(self) -> List[CategoryCount]:
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(_CATEGORIES_SQL)
                rows = cur.fetchall()

        return [
            CategoryCount(category=r["category"], count=int(r["count"]))
            for r in rows
        ]
