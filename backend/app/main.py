from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Civic issue reporting and resolution platform API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
    return response


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready", "database": "reachable"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
