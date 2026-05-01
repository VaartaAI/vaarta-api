from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_api_key
from app.cache import cached_json
from app.config import get_settings
from app.db import Database
from app.dependencies import get_db
from app.jwt_utils import optional_user
from app.repositories.feed import FeedRepository
from app.repositories.preferences import PreferencesRepository
from app.schemas.feed import FeedItem

VALID_CATEGORIES = {
    "politics", "business", "tech", "sports",
    "entertainment", "health", "science", "general",
}

router = APIRouter()


def _prefs_key(prefs: Optional[List[str]]) -> str:
    return ",".join(sorted(prefs)) if prefs else "none"


@router.get("/feed", response_model=List[FeedItem])
def get_feed(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    personalized: bool = Query(True),
    db: Database = Depends(get_db),
    user_id: Optional[int] = Depends(optional_user),
    _: str = Depends(require_api_key),
):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")

    settings = get_settings()
    preferred = None
    if not category and personalized and user_id is not None:
        preferred = PreferencesRepository(db).get_categories(user_id) or None

    cache_key = (
        f"feed:cat={category or 'none'}:p={page}:ps={page_size}"
        f":prefs={_prefs_key(preferred)}"
    )

    repo = FeedRepository(db)

    def _query():
        items = repo.get_feed(
            category=category,
            page=page,
            page_size=page_size,
            preferred_categories=preferred,
        )
        # serialize as plain dicts so cache can JSON-encode
        return [item.model_dump() for item in items]

    rows = cached_json(cache_key, settings.feed_cache_ttl_seconds, _query)
    return [FeedItem.model_validate(r) for r in rows]


@router.get("/search", response_model=List[FeedItem])
def search_feed(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
    _: str = Depends(require_api_key),
):
    repo = FeedRepository(db)
    return repo.search(query=q, page=page, page_size=page_size)
