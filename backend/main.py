"""PlagGuard – FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware import RateLimitMiddleware, RequestSizeLimitMiddleware
from backend.api.routes import router
from backend.config import settings
from backend.models.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

app = FastAPI(
    title="PlagGuard",
    description=(
        "Production-grade plagiarism detection, AI text detection, "
        "and text humanization API."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# ── Routes ─────────────────────────────────────────────────────────────
app.include_router(router)


# ── Startup ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    logging.getLogger(__name__).info("PlagGuard API ready 🛡️")
