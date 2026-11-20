import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationPublic
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.services.connection_manager import connection_manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/mine", response_model=list[NotificationPublic])
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)))

@router.patch("/{notification_id}/read", response_model=NotificationPublic)
def mark_read(notification_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Notification, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if item.user_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot update this notification")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket, token: str):
    user_id = decode_access_token(token)
    if user_id is None:
        await websocket.close(code=1008, reason="Invalid or expired access token")
        return

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            await websocket.close(code=1008, reason="User not found or inactive")
            return
        await connection_manager.connect(str(user.id), websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(str(user_id), websocket)
    except Exception:
        connection_manager.disconnect(str(user_id), websocket)
    finally:
        db.close()
