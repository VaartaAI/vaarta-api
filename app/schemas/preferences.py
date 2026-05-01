from typing import List
from pydantic import BaseModel, Field


class Preferences(BaseModel):
    categories: List[str] = Field(default_factory=list)


class UpdatePreferencesRequest(BaseModel):
    categories: List[str] = Field(min_length=1, max_length=12)
