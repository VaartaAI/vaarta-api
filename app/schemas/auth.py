from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    photo_url: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    id_token: str


class AuthResponse(BaseModel):
    token: str
    user: User
