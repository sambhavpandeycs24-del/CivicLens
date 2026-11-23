import json
import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Civic issue reporting and resolution platform API",
)

if settings.is_production:
    if settings.jwt_secret_key.startswith("unsafe-development") or len(settings.jwt_secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
    if "*" in settings.cors_origin_list:
        raise RuntimeError("Wildcard CORS origins are not allowed in production")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

logger = logging.getLogger("civiclens.request")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def production_request_controls(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    now = time.monotonic()
    client_ip = request.client.host if request.client else "unknown"
    bucket = _rate_buckets[client_ip]
    while bucket and now - bucket[0] > settings.rate_limit_window_seconds:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_requests:
        logger.info(json.dumps({
            "event": "request_rejected",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": 429,
        }))
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": str(settings.rate_limit_window_seconds), "X-Request-ID": request_id},
        )
    bucket.append(now)

    started = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - started) * 1000, 2)
    logger.info(json.dumps({
        "event": "http_request",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    }))
    response.headers.setdefault("X-Request-ID", request_id)
    return response


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data:; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    if settings.is_production:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    return response


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "reachable"}
    except Exception:
        logger.error(json.dumps({"event": "readiness_failed", "dependency": "database"}))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unreachable"},
        )


app.include_router(api_router, prefix=settings.api_v1_prefix)
