from fastapi import APIRouter, Depends

from app.db import Database
from app.dependencies import get_db
from app.jwt_utils import require_user
from app.repositories.preferences import PreferencesRepository
from app.schemas.preferences import Preferences, UpdatePreferencesRequest

router = APIRouter(prefix="/me/preferences", tags=["preferences"])


@router.get("", response_model=Preferences)
def get_my_preferences(
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    repo = PreferencesRepository(db)
    return Preferences(categories=repo.get_categories(user_id))


@router.put("", response_model=Preferences)
def update_my_preferences(
    body: UpdatePreferencesRequest,
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    repo = PreferencesRepository(db)
    saved = repo.replace_categories(user_id, body.categories)
    return Preferences(categories=saved)
