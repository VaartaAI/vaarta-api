from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_api_key
from app.db import Database
from app.dependencies import get_db
from app.repositories.feed import FeedRepository
from app.schemas.feed import FeedItem

VALID_CATEGORIES = {
    "politics", "business", "tech", "sports",
    "entertainment", "health", "science", "general",
}

router = APIRouter()


@router.get("/feed", response_model=List[FeedItem])
def get_feed(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
    _: str = Depends(require_api_key),
):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    repo = FeedRepository(db)
    return repo.get_feed(category=category, page=page, page_size=page_size)
