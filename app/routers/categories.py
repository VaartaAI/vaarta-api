from typing import List

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.db import Database
from app.dependencies import get_db
from app.repositories.categories import CategoryRepository
from app.schemas.categories import CategoryCount

router = APIRouter()


@router.get("/categories", response_model=List[CategoryCount])
def get_categories(
    db: Database = Depends(get_db),
    _: str = Depends(require_api_key),
):
    repo = CategoryRepository(db)
    return repo.get_counts()
