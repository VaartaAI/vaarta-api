from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Database
from app.dependencies import _get_db
from app.exceptions import http_exception_handler, unhandled_exception_handler
from app.routers import feed, story, categories
from fastapi.exceptions import HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly initialise the connection pool on startup.
    settings = get_settings()
    _get_db(settings)
    yield
    # Gracefully close the pool on shutdown.
    db: Database = _get_db(settings)
    db.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(feed.router)
    app.include_router(story.router)
    app.include_router(categories.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
