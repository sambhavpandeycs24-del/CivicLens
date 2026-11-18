from fastapi import APIRouter
<<<<<<< HEAD
from app.api.v1.endpoints import admin, auth, users, complaints, ai, analytics, geo, notifications
=======
from app.api.v1.endpoints import admin, auth, users, complaints
>>>>>>> 0c4b4f0250554b1fa35b48a3453e45be6be0c369

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(complaints.router)
<<<<<<< HEAD
api_router.include_router(ai.router)

api_router.include_router(analytics.router)
api_router.include_router(geo.router)
api_router.include_router(notifications.router)
=======
>>>>>>> 0c4b4f0250554b1fa35b48a3453e45be6be0c369
