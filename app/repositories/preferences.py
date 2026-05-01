from typing import List
from psycopg2.extras import RealDictCursor

from app.db import Database


class PreferencesRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_categories(self, user_id: int) -> List[str]:
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT category FROM user_preferences WHERE user_id = %s ORDER BY rank, category",
                    (user_id,),
                )
                return [r["category"] for r in cur.fetchall()]

    def replace_categories(self, user_id: int, categories: List[str]) -> List[str]:
        """Replace the user's preferences atomically."""
        with self._db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
                if categories:
                    values = [(user_id, cat, idx) for idx, cat in enumerate(categories)]
                    cur.executemany(
                        "INSERT INTO user_preferences (user_id, category, rank) VALUES (%s, %s, %s)",
                        values,
                    )
        return list(categories)
