from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.complaint import Complaint, ComplaintStatus, ComplaintCategory
from app.models.user import User, UserRole

router = APIRouter(prefix="/analytics", tags=["Civic Analytics"])

@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN))):
    base = select(Complaint)
    if user.role == UserRole.AUTHORITY:
        base = base.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    status_rows = db.execute(select(Complaint.status, func.count(Complaint.id)).where(
        (Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)) if user.role == UserRole.AUTHORITY else True
    ).group_by(Complaint.status)).all()
    category_rows = db.execute(select(Complaint.category, func.count(Complaint.id)).where(
        (Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)) if user.role == UserRole.AUTHORITY else True
    ).group_by(Complaint.category)).all()
    scope = ((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None))) if user.role == UserRole.AUTHORITY else True
    resolved = db.scalar(select(func.count(Complaint.id)).where(scope, Complaint.status == ComplaintStatus.RESOLVED)) or 0
    rejected = db.scalar(select(func.count(Complaint.id)).where(scope, Complaint.status == ComplaintStatus.REJECTED)) or 0
    open_count = total - resolved - rejected
    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "open_complaints": open_count,
        "resolution_rate_percent": round((resolved / total) * 100, 2) if total else 0,
        "by_status": {str(k.value): v for k, v in status_rows},
        "by_category": {str(k.value): v for k, v in category_rows},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
