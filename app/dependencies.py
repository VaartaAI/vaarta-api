from functools import lru_cache
from typing import Generator

from fastapi import Depends

from app.config import Settings, get_settings
from app.db import Database


@lru_cache(maxsize=1)
def _get_db(settings: Settings) -> Database:
    return Database(settings)


def get_db(settings: Settings = Depends(get_settings)) -> Database:
    return _get_db(settings)
