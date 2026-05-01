from typing import Optional
from psycopg2.extras import RealDictCursor

from app.db import Database
from app.schemas.auth import User


def _row_to_user(r: dict) -> User:
    return User(
        id=r["id"],
        email=r["email"],
        name=r.get("name"),
        photo_url=r.get("photo_url"),
    )


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, email, name, photo_url FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
        return _row_to_user(row) if row else None

    def upsert_by_google_sub(
        self,
        google_sub: str,
        email: str,
        name: Optional[str],
        photo_url: Optional[str],
    ) -> User:
        """
        Insert if new, otherwise update profile fields. Always returns the user.
        """
        sql = """
            INSERT INTO users (google_sub, email, name, photo_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (google_sub) DO UPDATE
              SET email      = EXCLUDED.email,
                  name       = COALESCE(EXCLUDED.name,      users.name),
                  photo_url  = COALESCE(EXCLUDED.photo_url, users.photo_url),
                  updated_at = CURRENT_TIMESTAMP
            RETURNING id, email, name, photo_url
        """
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (google_sub, email, name, photo_url))
                row = cur.fetchone()
        return _row_to_user(row)
