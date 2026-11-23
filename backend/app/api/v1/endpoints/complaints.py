import secrets
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus, ComplaintCategory, ComplaintPriority
from app.schemas.complaint import ComplaintCreate, ComplaintPublic, ComplaintUpdate
from app.models.notification import Notification
from app.services.connection_manager import connection_manager
from app.services.ai_assistant import find_duplicates

router = APIRouter(prefix="/complaints", tags=["Complaints"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ("jpg", "jpeg", b"\xff\xd8\xff"),
    "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": ("webp", b"RIFF"),
}


def _image_authorized(complaint: Complaint, user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.CITIZEN:
        return complaint.reporter_id == user.id
    return complaint.assigned_to_id in (None, user.id)


def _validate_image_signature(content_type: str | None, filename: str | None, first_bytes: bytes) -> tuple[str, str]:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP images are supported")
    extension = (Path(filename or "").suffix.lower().lstrip("."))
    allowed = ALLOWED_IMAGE_TYPES[content_type]
    valid_extensions = allowed[:-1] if content_type == "image/jpeg" else allowed[:-1]
    if content_type == "image/jpeg":
        valid_extensions = ("jpg", "jpeg")
        signature_valid = first_bytes.startswith(allowed[-1])
    elif content_type == "image/png":
        valid_extensions = ("png",)
        signature_valid = first_bytes.startswith(allowed[-1])
    else:
        valid_extensions = ("webp",)
        signature_valid = (
            len(first_bytes) >= 12
            and first_bytes.startswith(b"RIFF")
            and first_bytes[8:12] == b"WEBP"
        )
    if extension not in valid_extensions:
        raise HTTPException(status_code=415, detail="File extension does not match the supported image type")
    if not signature_valid:
        raise HTTPException(status_code=415, detail="File content is not a valid supported image")
    return extension, valid_extensions[0]

def _tracking_code():
    return "CL-" + secrets.token_hex(4).upper()

@router.post("", response_model=ComplaintPublic, status_code=status.HTTP_201_CREATED)
async def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    complaint = Complaint(**payload.model_dump(), reporter_id=user.id, tracking_code=_tracking_code())
    db.add(complaint)
    db.flush()
    db.add(Notification(user_id=user.id, complaint_id=complaint.id, title="Complaint submitted", message=f"Your complaint {complaint.tracking_code} has been submitted successfully."))
    db.commit()
    db.refresh(complaint)
    await connection_manager.broadcast_user(str(user.id), {
        "title": "Complaint submitted",
        "message": f"Your complaint {complaint.tracking_code} has been submitted successfully.",
        "complaint_id": str(complaint.id),
    })
    return complaint

@router.get("/mine", response_model=list[ComplaintPublic])
def my_complaints(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Complaint).where(Complaint.reporter_id == user.id).order_by(Complaint.created_at.desc())))

@router.get("", response_model=list[ComplaintPublic])
def list_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    category: ComplaintCategory | None = Query(default=None),
    priority: ComplaintPriority | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    query = select(Complaint).order_by(Complaint.created_at.desc())
    if status_filter:
        query = query.where(Complaint.status == status_filter)
    if category:
        query = query.where(Complaint.category == category)
    if priority:
        query = query.where(Complaint.priority == priority)
    if user.role == UserRole.AUTHORITY:
        query = query.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
    return list(db.scalars(query))

@router.get("/{complaint_id}", response_model=ComplaintPublic)
def get_complaint(complaint_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if user.role == UserRole.CITIZEN and complaint.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot view this complaint")
    if user.role == UserRole.AUTHORITY and complaint.assigned_to_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Complaint is assigned to another authority")
    return complaint

@router.patch("/{complaint_id}", response_model=ComplaintPublic)
async def update_complaint(
    complaint_id: uuid.UUID,
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
    if "status" in changes:
        if complaint.status == ComplaintStatus.RESOLVED and old_status != ComplaintStatus.RESOLVED:
            complaint.resolved_at = datetime.now(timezone.utc)
        elif old_status == ComplaintStatus.RESOLVED and complaint.status != ComplaintStatus.RESOLVED:
            complaint.resolved_at = None
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
    if complaint.status != old_status:
        await connection_manager.broadcast_user(str(complaint.reporter_id), {
            "title": "Complaint status updated",
            "message": f"Your complaint {complaint.tracking_code} is now {complaint.status.value.replace('_', ' ')}.",
            "complaint_id": str(complaint.id),
        })
    if complaint.assigned_to_id and complaint.assigned_to_id != old_assignee:
        await connection_manager.broadcast_user(str(complaint.assigned_to_id), {
            "title": "Complaint assigned to you",
            "message": f"Complaint {complaint.tracking_code} has been assigned to you.",
            "complaint_id": str(complaint.id),
        })
    return complaint


@router.get("/{complaint_id}/duplicates")
def complaint_duplicates(
    complaint_id: uuid.UUID,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    candidates = find_duplicates(
        db,
        complaint.title,
        complaint.description,
        complaint.category,
        complaint.latitude,
        complaint.longitude,
        limit=limit,
    )
    candidates = [candidate for candidate in candidates if candidate["complaint_id"] != str(complaint.id)]
    return {
        "complaint_id": str(complaint.id),
        "tracking_code": complaint.tracking_code,
        "possible_duplicates": candidates,
        "advisory": "Possible matches require human review; complaints are never merged automatically.",
    }


@router.post("/{complaint_id}/image", response_model=ComplaintPublic)
async def upload_complaint_image(
    complaint_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if not _image_authorized(complaint, user):
        raise HTTPException(status_code=403, detail="You cannot upload an image for this complaint")

    first_bytes = await file.read(12)
    extension, canonical_extension = _validate_image_signature(file.content_type, file.filename, first_bytes)
    storage_dir = Path(settings.complaint_upload_dir).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_key = f"{uuid.uuid4().hex}.{canonical_extension}"
    destination = (storage_dir / storage_key).resolve()
    if destination.parent != storage_dir:
        raise HTTPException(status_code=500, detail="Invalid upload storage path")

    size = len(first_bytes)
    try:
        with destination.open("xb") as output:
            output.write(first_bytes)
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.complaint_upload_max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Image exceeds the maximum allowed size of {settings.complaint_upload_max_bytes} bytes",
                    )
                output.write(chunk)
    except HTTPException:
        if destination.exists():
            destination.unlink()
        raise
    except Exception:
        if destination.exists():
            destination.unlink()
        raise HTTPException(status_code=500, detail="Could not store uploaded image")

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    complaint.image_storage_key = storage_key
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/{complaint_id}/image")
def get_complaint_image(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if not _image_authorized(complaint, user):
        raise HTTPException(status_code=403, detail="You cannot view this complaint image")

    if complaint.image_storage_key:
        storage_dir = Path(settings.complaint_upload_dir).resolve()
        key_path = Path(complaint.image_storage_key)
        if key_path.name != complaint.image_storage_key:
            raise HTTPException(status_code=500, detail="Invalid stored image reference")
        image_path = (storage_dir / key_path.name).resolve()
        if image_path.parent != storage_dir or not image_path.is_file():
            raise HTTPException(status_code=404, detail="Uploaded image not found")
        return FileResponse(image_path, filename=image_path.name)
    if complaint.image_url:
        return RedirectResponse(url=complaint.image_url)
    raise HTTPException(status_code=404, detail="Complaint image not found")
