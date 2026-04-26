from typing import List, Optional

from app.db import Database
from app.schemas.feed import FeedItem

_FEED_SQL = """
    SELECT s.id, s.cluster_id, s.summary_text, s.category, s.created_at,
        (SELECT a.title FROM articles a WHERE a.cluster_id = s.cluster_id ORDER BY a.published_at DESC LIMIT 1) AS headline,
        (SELECT COUNT(*) FROM articles a WHERE a.cluster_id = s.cluster_id) AS source_count
    FROM summaries s WHERE s.is_safe = true {category_filter}
    ORDER BY s.created_at DESC LIMIT %s OFFSET %s
"""


class FeedRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_feed(
        self,
        category: Optional[str],
        page: int,
        page_size: int,
    ) -> List[FeedItem]:
        offset = (page - 1) * page_size
        if category:
            sql = _FEED_SQL.format(category_filter="AND s.category = %s")
            params = (category, page_size, offset)
        else:
            sql = _FEED_SQL.format(category_filter="")
            params = (page_size, offset)

        with self._db.get_conn() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        return [
            FeedItem(
                id=r["id"],
                cluster_id=r["cluster_id"],
                headline=r["headline"] or "Untitled",
                summary=r["summary_text"],
                category=r["category"],
                source_count=int(r["source_count"]),
                created_at=r["created_at"].isoformat(),
            )
            for r in rows
        ]
