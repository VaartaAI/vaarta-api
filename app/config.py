from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    app_title: str = "VaartaAI API"
    app_version: str = "1.0.0"
    db_pool_min: int = 1
    db_pool_max: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
