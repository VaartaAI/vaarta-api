import json
from typing import List, Optional

from psycopg2.extras import RealDictCursor

from app.db import Database
from app.schemas.story import SourceOut, StoryDetail

_STORY_SQL = """
    SELECT s.id, s.cluster_id, s.summary_text, s.why_it_matters, s.deep_explainer,
        s.category, s.entities, s.topics, s.sources_agree, s.created_at,
        (SELECT a.title FROM articles a WHERE a.cluster_id = s.cluster_id ORDER BY a.published_at DESC LIMIT 1) AS headline,
        (SELECT a.image_url FROM articles a WHERE a.cluster_id = s.cluster_id AND a.image_url IS NOT NULL ORDER BY a.published_at DESC LIMIT 1) AS image_url
    FROM summaries s WHERE s.cluster_id = %s AND s.is_safe = true
"""

_SOURCES_SQL = """
    SELECT DISTINCT src.name, src.trust_score FROM articles a
    JOIN sources src ON src.id = a.source_id WHERE a.cluster_id = %s ORDER BY src.trust_score DESC
"""


def _parse_json_field(val) -> List:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except Exception:
        return []


class StoryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_story(self, cluster_id: int) -> Optional[StoryDetail]:
        with self._db.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(_STORY_SQL, (cluster_id,))
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute(_SOURCES_SQL, (cluster_id,))
                source_rows = cur.fetchall()

        sources = [
            SourceOut(name=s["name"], trust_score=s["trust_score"])
            for s in source_rows
        ]
        return StoryDetail(
            id=row["id"],
            cluster_id=row["cluster_id"],
            headline=row["headline"] or "Untitled",
            summary=row["summary_text"],
            why_it_matters=row["why_it_matters"],
            background=row["deep_explainer"],
            category=row["category"],
            entities=_parse_json_field(row["entities"]),
            topics=_parse_json_field(row["topics"]),
            sources_agree=row["sources_agree"],
            created_at=row["created_at"].isoformat(),
            sources=sources,
            image_url=row.get("image_url"),
        )
