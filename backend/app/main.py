"""FastAPI application entry point.

Lifespan: pre-warms both spaCy models on startup so the first real request
doesn't suffer a cold-start delay.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up the NLP models once at startup."""
    import logging

    logger = logging.getLogger("setu.startup")

    try:
        from app.extraction.criteria_extractor import get_nlp as get_sm
        get_sm()
        logger.info("spaCy en_core_web_sm loaded ✓")
    except Exception as exc:
        logger.warning("Could not pre-load en_core_web_sm: %s", exc)

    try:
        from app.matching.embedder import get_model
        if get_model() is not None:
            logger.info("Sentence-transformer embedding model loaded ✓")
        else:
            logger.warning(
                "Sentence-transformer embedding model unavailable — "
                "semantic scoring will fall back to neutral"
            )
    except Exception as exc:
        logger.warning("Could not pre-load embedding model: %s", exc)

    yield  # Application runs here


app = FastAPI(
    title="Setu API",
    description="AI-powered government scheme & opportunity discovery platform",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow the Vite dev server (and any future production origin set via env var)
import os

_origins_env = os.getenv("SETU_ALLOWED_ORIGINS", "")
_extra_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    # Allow all common Vite dev-server ports (5173 is default, but Vite
    # increments automatically if the port is busy: 5174, 5175, …)
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ] + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
