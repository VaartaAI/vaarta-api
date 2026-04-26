from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    settings = get_settings()
    if not settings.api_key:
        # No key configured — open access (development mode)
        return ""
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
