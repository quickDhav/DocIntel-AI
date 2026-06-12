"""FastAPI application entry point.

Creates the app instance, configures middleware, includes routers, and
sets up startup events for database initialisation and storage
directory creation.
"""

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db

logger = logging.getLogger(__name__)
settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Document Intelligence backend …")

    settings.ensure_directories()
    logger.info("Storage directories ensured")

    init_db()
    logger.info("Database initialised")

    from app.utils.encryption import FileEncryption
    FileEncryption()  # triggers key auto-generation on first run

    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down")



app = FastAPI(
    title="Document Intelligence — Agentic RAG",
    description=(
        "Upload documents, extract content with OCR, classify with AI, "
        "and ask questions with cited answers powered by RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject standard security headers into every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response



_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX_REQUESTS = 120  # per window


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic in-memory rate limiter keyed by client IP.

    Allows ``_RATE_LIMIT_MAX_REQUESTS`` requests per
    ``_RATE_LIMIT_WINDOW``-second window per IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    timestamps = _rate_limit_store[client_ip]
    _rate_limit_store[client_ip] = [
        ts for ts in timestamps if now - ts < _RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX_REQUESTS:
        return Response(
            content='{"detail":"Rate limit exceeded. Try again later."}',
            status_code=429,
            media_type="application/json",
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)



from app.routers import upload, chat, documents, pages  # noqa: E402

app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(pages.router, prefix="/api")



@app.get("/api/health", tags=["health"])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Document Intelligence — Agentic RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
