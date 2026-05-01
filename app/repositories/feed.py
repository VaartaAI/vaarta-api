from typing import List, Optional

from app.db import Database
from app.schemas.feed import FeedItem

_BASE_SELECT = """
    SELECT s.id, s.cluster_id, s.summary_text, s.category, s.created_at,
        (SELECT a.title FROM articles a WHERE a.cluster_id = s.cluster_id ORDER BY a.published_at DESC LIMIT 1) AS headline,
        (SELECT COUNT(*) FROM articles a WHERE a.cluster_id = s.cluster_id) AS source_count,
        (SELECT a.image_url FROM articles a WHERE a.cluster_id = s.cluster_id AND a.image_url IS NOT NULL ORDER BY a.published_at DESC LIMIT 1) AS image_url
    FROM summaries s WHERE s.is_safe = true
"""


def _row_to_feed_item(r: dict) -> FeedItem:
    return FeedItem(
        id=r["id"],
        cluster_id=r["cluster_id"],
        headline=r["headline"] or "Untitled",
        summary=r["summary_text"],
        category=r["category"],
        source_count=int(r["source_count"]),
        created_at=r["created_at"].isoformat(),
        image_url=r.get("image_url"),
    )


class FeedRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _fetch(self, sql: str, params: tuple) -> List[FeedItem]:
        with self._db.get_conn() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return [_row_to_feed_item(r) for r in cur.fetchall()]

    def get_feed(
        self,
        category: Optional[str],
        page: int,
        page_size: int,
        preferred_categories: Optional[List[str]] = None,
    ) -> List[FeedItem]:
        offset = (page - 1) * page_size
        if category:
            sql = _BASE_SELECT + "AND s.category = %s ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
            params = (category, page_size, offset)
        elif preferred_categories:
            placeholders = ",".join(["%s"] * len(preferred_categories))
            sql = (
                _BASE_SELECT
                + f"AND s.category IN ({placeholders}) "
                + "ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
            )
            params = (*preferred_categories, page_size, offset)
        else:
            sql = _BASE_SELECT + "ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
            params = (page_size, offset)
        return self._fetch(sql, params)

    def search(self, query: str, page: int, page_size: int) -> List[FeedItem]:
        offset = (page - 1) * page_size
        sql = (
            _BASE_SELECT +
            """AND (
                s.summary_text ILIKE %s OR
                EXISTS (
                    SELECT 1 FROM articles a
                    WHERE a.cluster_id = s.cluster_id AND a.title ILIKE %s
                )
            )
            ORDER BY s.created_at DESC LIMIT %s OFFSET %s"""
        )
        like = f"%{query}%"
        return self._fetch(sql, (like, like, page_size, offset))
