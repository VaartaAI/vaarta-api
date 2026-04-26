from typing import List

from fastapi import APIRouter, Depends

from app.db import Database
from app.dependencies import get_db
from app.repositories.categories import CategoryRepository
from app.schemas.categories import CategoryCount

router = APIRouter()


@router.get("/categories", response_model=List[CategoryCount])
def get_categories(db: Database = Depends(get_db)):
    repo = CategoryRepository(db)
    return repo.get_counts()
