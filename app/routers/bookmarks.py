from fastapi import APIRouter, Depends, Query

from app.db import Database
from app.dependencies import get_db
from app.jwt_utils import require_user
from app.repositories.bookmarks import BookmarksRepository
from app.schemas.bookmarks import BookmarkRequest, BookmarkList, BookmarkIds

router = APIRouter(prefix="/me/bookmarks", tags=["bookmarks"])


@router.get("/ids", response_model=BookmarkIds)
def list_bookmark_ids(
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    repo = BookmarksRepository(db)
    return BookmarkIds(cluster_ids=repo.cluster_ids(user_id))


@router.get("", response_model=BookmarkList)
def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    repo = BookmarksRepository(db)
    return BookmarkList(items=repo.list_items(user_id, page, page_size))


@router.post("")
def add_bookmark(
    body: BookmarkRequest,
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    BookmarksRepository(db).add(user_id, body.cluster_id)
    return {"ok": True}


@router.delete("/{cluster_id}")
def remove_bookmark(
    cluster_id: int,
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    BookmarksRepository(db).remove(user_id, cluster_id)
    return {"ok": True}
