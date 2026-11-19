import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint import ComplaintCreate, ComplaintPublic, ComplaintUpdate
from app.models.notification import Notification

router = APIRouter(prefix="/complaints", tags=["Complaints"])

def _tracking_code():
    return "CL-" + secrets.token_hex(4).upper()

@router.post("", response_model=ComplaintPublic, status_code=status.HTTP_201_CREATED)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    complaint = Complaint(**payload.model_dump(), reporter_id=user.id, tracking_code=_tracking_code())
    db.add(complaint)
    db.flush()
    db.add(Notification(user_id=user.id, complaint_id=complaint.id, title="Complaint submitted", message=f"Your complaint {complaint.tracking_code} has been submitted successfully."))
    db.commit()
    db.refresh(complaint)
    return complaint

@router.get("/mine", response_model=list[ComplaintPublic])
def my_complaints(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Complaint).where(Complaint.reporter_id == user.id).order_by(Complaint.created_at.desc())))

@router.get("", response_model=list[ComplaintPublic])
def list_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    query = select(Complaint).order_by(Complaint.created_at.desc())
    if status_filter:
        query = query.where(Complaint.status == status_filter)
    if user.role == UserRole.AUTHORITY:
        query = query.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
    return list(db.scalars(query))

@router.get("/{complaint_id}", response_model=ComplaintPublic)
def get_complaint(complaint_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if user.role == UserRole.CITIZEN and complaint.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot view this complaint")
    if user.role == UserRole.AUTHORITY and complaint.assigned_to_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Complaint is assigned to another authority")
    return complaint

@router.patch("/{complaint_id}", response_model=ComplaintPublic)
def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    changes = payload.model_dump(exclude_unset=True)
    old_status = complaint.status
    old_assignee = complaint.assigned_to_id
    if "assigned_to_id" in changes and changes["assigned_to_id"] is not None:
        assignee = db.get(User, changes["assigned_to_id"])
        if assignee is None or assignee.role != UserRole.AUTHORITY or not assignee.is_active:
            raise HTTPException(status_code=422, detail="Assignee must be an active authority user")
    if changes.get("status") == ComplaintStatus.RESOLVED and not changes.get("resolution_note", complaint.resolution_note):
        raise HTTPException(status_code=422, detail="Resolution note is required to resolve a complaint")
    for key, value in changes.items():
        setattr(complaint, key, value)
    if complaint.assigned_to_id and complaint.status == ComplaintStatus.SUBMITTED:
        complaint.status = ComplaintStatus.ASSIGNED
    db.flush()
    if complaint.status != old_status:
        db.add(Notification(user_id=complaint.reporter_id, complaint_id=complaint.id,
            title="Complaint status updated", message=f"Your complaint {complaint.tracking_code} is now {complaint.status.value.replace('_', ' ')}."))
    if complaint.assigned_to_id and complaint.assigned_to_id != old_assignee:
        db.add(Notification(user_id=complaint.assigned_to_id, complaint_id=complaint.id,
            title="Complaint assigned to you", message=f"Complaint {complaint.tracking_code} has been assigned to you."))
    db.commit()
    db.refresh(complaint)
    return complaint
