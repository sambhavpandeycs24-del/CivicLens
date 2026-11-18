from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0", description="Civic issue reporting and resolution platform API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.app_name}
