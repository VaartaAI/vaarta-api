from pydantic import BaseModel


class CategoryCount(BaseModel):
    category: str
    count: int
