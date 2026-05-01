from typing import List
from psycopg2.extras import RealDictCursor

from app.db import Database
from app.schemas.feed import FeedItem
from app.repositories.feed import _row_to_feed_item


class BookmarksRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, user_id: int, cluster_id: int) -> None:
        with self._db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bookmarks (user_id, cluster_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """,
                    (user_id, cluster_id),
                )

    def remove(self, user_id: int, cluster_id: int) -> None:
        with self._db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM bookmarks WHERE user_id = %s AND cluster_id = %s",
                    (user_id, cluster_id),
                )

    def cluster_ids(self, user_id: int) -> List[int]:
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT cluster_id FROM bookmarks WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,),
                )
                return [r["cluster_id"] for r in cur.fetchall()]

    def list_items(self, user_id: int, page: int, page_size: int) -> List[FeedItem]:
        offset = (page - 1) * page_size
        sql = """
            SELECT s.id, s.cluster_id, s.summary_text, s.why_it_matters, s.category, s.created_at,
                (SELECT a.title    FROM articles a WHERE a.cluster_id = s.cluster_id ORDER BY a.published_at DESC LIMIT 1) AS headline,
                (SELECT COUNT(*)   FROM articles a WHERE a.cluster_id = s.cluster_id) AS source_count,
                (SELECT a.image_url FROM articles a WHERE a.cluster_id = s.cluster_id AND a.image_url IS NOT NULL ORDER BY a.published_at DESC LIMIT 1) AS image_url
            FROM bookmarks b
            JOIN summaries s ON s.cluster_id = b.cluster_id AND s.is_safe = true
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s
        """
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (user_id, page_size, offset))
                return [_row_to_feed_item(r) for r in cur.fetchall()]
