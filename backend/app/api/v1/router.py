from fastapi import APIRouter
from app.api.v1.endpoints import admin, auth, users, complaints, ai, analytics, geo, notifications

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(complaints.router)
api_router.include_router(ai.router)

api_router.include_router(analytics.router)
api_router.include_router(geo.router)
api_router.include_router(notifications.router)
