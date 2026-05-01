from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import Settings, get_settings
from app.db import Database
from app.dependencies import get_db
from app.jwt_utils import issue_token, require_user
from app.repositories.users import UserRepository
from app.schemas.auth import AuthResponse, GoogleAuthRequest, User

router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_google_id_token(token: str, audience: str) -> dict:
    """
    Verifies Google ID token signature + audience. Returns decoded payload.
    """
    try:
        info = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audience,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {e}",
        )

    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
        )
    return info


@router.post("/google", response_model=AuthResponse)
def login_with_google(
    body: GoogleAuthRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    info = _verify_google_id_token(body.id_token, settings.google_web_client_id)

    google_sub = info["sub"]
    email = info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email",
        )

    repo = UserRepository(db)
    user = repo.upsert_by_google_sub(
        google_sub=google_sub,
        email=email,
        name=info.get("name"),
        photo_url=info.get("picture"),
    )

    token = issue_token(user.id, user.email, settings)
    return AuthResponse(token=token, user=user)


@router.get("/me", response_model=User)
def get_me(
    user_id: int = Depends(require_user),
    db: Database = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
