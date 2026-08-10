"""FastAPI application entrypoint (PRD Ch4.5 / Ch18.2 request lifecycle)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, logger
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(debug=settings.debug)
    logger.info("CliniScribe AI backend starting", extra={"route": "startup"})
    yield
    logger.info("CliniScribe AI backend shutting down", extra={"route": "shutdown"})


def create_app() -> FastAPI:
    app = FastAPI(
        title="CliniScribe AI API",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
