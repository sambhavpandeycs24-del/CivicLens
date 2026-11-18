from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationPublic

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/mine", response_model=list[NotificationPublic])
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)))

@router.patch("/{notification_id}/read", response_model=NotificationPublic)
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Notification, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if item.user_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot update this notification")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item
