from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Database
from app.dependencies import _get_db
from app.exceptions import http_exception_handler, unhandled_exception_handler
from app.routers import feed, story, categories, auth
from fastapi.exceptions import HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_db()       # warm up connection pool on startup
    yield
    _get_db().close()   # gracefully close on shutdown


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
    app.include_router(auth.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
