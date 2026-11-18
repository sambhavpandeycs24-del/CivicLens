from fastapi import APIRouter, Depends
from app.api.deps import require_roles
from app.models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/role-check")
def role_check(current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.AUTHORITY))):
    return {"message": "Role access granted", "role": current_user.role.value}
