"""FastAPI application — HireScope AI backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hiring_engine.config import get_settings
from hiring_engine.logging_config import setup_logging
from api.routers import candidate, hiring, github, health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("HireScope AI starting up (env=%s)", settings.environment)

    # Preload embedding model so first request isn't slow
    from api.dependencies import get_skill_matcher
    get_skill_matcher()

    yield
    logger.info("HireScope AI shutting down")


app = FastAPI(
    title="HireScope AI",
    description="AI-powered hiring platform with multi-agent debate system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(candidate.router, prefix="/api/candidate", tags=["candidate"])
app.include_router(hiring.router, prefix="/api/hiring", tags=["hiring"])
app.include_router(github.router, prefix="/api/github", tags=["github"])


@app.get("/")
async def root():
    return {
        "service": "HireScope AI",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
