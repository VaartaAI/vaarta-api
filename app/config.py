from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    api_key: str = ""          # Set this in production to restrict access
    app_title: str = "VaartaAI API"
    app_version: str = "1.0.0"
    db_pool_min: int = 1
    db_pool_max: int = 5

    # ── Auth ───────────────────────────────────────────────────────
    jwt_secret: str                     # required — long random string
    jwt_algorithm: str = "HS256"
    jwt_expires_days: int = 30
    google_web_client_id: str           # OAuth web client ID for ID token verification

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
