from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import os
import json
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# DB pool
# ---------------------------------------------------------------------------
_pool: psycopg2.pool.SimpleConnectionPool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            1, 5, dsn=os.environ["DATABASE_URL"]
        )
    return _pool


def query(sql: str, params: tuple = None) -> list:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.fetchall()
    finally:
        pool.putconn(conn)


def query_one(sql: str, params: tuple = None) -> Optional[dict]:
    rows = query(sql, params)
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    get_pool()          # warm up connection pool on startup
    yield
    if _pool:
        _pool.closeall()


app = FastAPI(title="VaartaAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class SourceOut(BaseModel):
    name: str
    trust_score: float


class FeedItem(BaseModel):
    id: int
    cluster_id: int
    headline: str
    summary: str
    category: str
    source_count: int
    created_at: str


class StoryDetail(BaseModel):
    id: int
    cluster_id: int
    headline: str
    summary: str
    why_it_matters: str
    background: Optional[str]
    category: str
    entities: List[str]
    topics: List[str]
    sources_agree: bool
    created_at: str
    sources: list


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
VALID_CATEGORIES = {
    "politics", "business", "tech", "sports",
    "entertainment", "health", "science", "general"
}


def _parse_json_field(val):
    if val is None:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/feed", response_model=list[FeedItem])
def get_feed(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}")

    offset = (page - 1) * page_size

    category_filter = "AND s.category = %s" if category else ""
    params = [page_size, offset]
    if category:
        params = [category, page_size, offset]

    rows = query(
        f"""
        SELECT
            s.id,
            s.cluster_id,
            s.summary_text,
            s.category,
            s.created_at,
            (
                SELECT a.title
                FROM articles a
                WHERE a.cluster_id = s.cluster_id
                ORDER BY a.published_at DESC
                LIMIT 1
            ) AS headline,
            (
                SELECT COUNT(*)
                FROM articles a
                WHERE a.cluster_id = s.cluster_id
            ) AS source_count
        FROM summaries s
        WHERE s.is_safe = true
        {category_filter}
        ORDER BY s.created_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )

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


@app.get("/story/{cluster_id}", response_model=StoryDetail)
def get_story(cluster_id: int):
    row = query_one(
        """
        SELECT
            s.id,
            s.cluster_id,
            s.summary_text,
            s.why_it_matters,
            s.deep_explainer,
            s.category,
            s.entities,
            s.topics,
            s.sources_agree,
            s.created_at,
            (
                SELECT a.title
                FROM articles a
                WHERE a.cluster_id = s.cluster_id
                ORDER BY a.published_at DESC
                LIMIT 1
            ) AS headline
        FROM summaries s
        WHERE s.cluster_id = %s AND s.is_safe = true
        """,
        (cluster_id,),
    )

    if not row:
        raise HTTPException(404, "Story not found")

    sources = query(
        """
        SELECT DISTINCT src.name, src.trust_score
        FROM articles a
        JOIN sources src ON src.id = a.source_id
        WHERE a.cluster_id = %s
        ORDER BY src.trust_score DESC
        """,
        (cluster_id,),
    )

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
        sources=[SourceOut(name=s["name"], trust_score=s["trust_score"]) for s in sources],
    )


@app.get("/categories")
def get_categories():
    rows = query(
        """
        SELECT category, COUNT(*) as count
        FROM summaries
        WHERE is_safe = true
        GROUP BY category
        ORDER BY count DESC
        """
    )
    return [{"category": r["category"], "count": int(r["count"])} for r in rows]
