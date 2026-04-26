from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from app.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self._pool = psycopg2.pool.SimpleConnectionPool(
            settings.db_pool_min,
            settings.db_pool_max,
            dsn=settings.database_url,
        )

    @contextmanager
    def get_conn(self) -> Generator:
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        self._pool.closeall()

    def query(self, sql: str, params=None):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def query_one(self, sql: str, params=None):
        rows = self.query(sql, params)
        return rows[0] if rows else None
