import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import DepartmentUpdate

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/role-check")
def role_check(current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.AUTHORITY))):
    return {"message": "Role access granted", "role": current_user.role.value}


@router.patch("/users/{user_id}/department")
def update_user_department(
    user_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.AUTHORITY:
        raise HTTPException(status_code=422, detail="Departments can only be assigned to authority users")
    department = payload.department.strip() if payload.department else None
    user.department = department or None
    db.commit()
    return {"user_id": str(user.id), "department": user.department}
