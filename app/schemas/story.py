from typing import List, Optional

from pydantic import BaseModel


class SourceOut(BaseModel):
    name: str
    trust_score: float


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
    sources: List[SourceOut]
