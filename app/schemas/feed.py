from typing import Optional

from pydantic import BaseModel


class FeedItem(BaseModel):
    id: int
    cluster_id: int
    headline: str
    summary: str
    category: str
    source_count: int
    created_at: str
    image_url: Optional[str] = None
