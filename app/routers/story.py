from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_api_key
from app.db import Database
from app.dependencies import get_db
from app.repositories.story import StoryRepository
from app.schemas.story import StoryDetail

router = APIRouter()


@router.get("/story/{cluster_id}", response_model=StoryDetail)
def get_story(
    cluster_id: int,
    db: Database = Depends(get_db),
    _: str = Depends(require_api_key),
):
    repo = StoryRepository(db)
    story = repo.get_story(cluster_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return story
