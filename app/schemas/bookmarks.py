from typing import List
from pydantic import BaseModel
from app.schemas.feed import FeedItem


class BookmarkRequest(BaseModel):
    cluster_id: int


class BookmarkList(BaseModel):
    items: List[FeedItem]


class BookmarkIds(BaseModel):
    cluster_ids: List[int]
