from app.config import get_settings
from app.db import Database

_db: Database = None


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(get_settings())
    return _db


def get_db() -> Database:
    return _get_db()
