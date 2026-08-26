from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.core.security import get_current_user


# =========================================================
# Notification Router
# =========================================================

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# =========================================================
# GET USER NOTIFICATIONS
# =========================================================

@router.get("/")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user == current_user.id
        )
        .order_by(
            Notification.timestamp.desc()
        )
        .all()
    )

    return {
        "message": "Notifications fetched successfully",
        "notifications": [
            {
                "id": notification.id,
                "user": notification.user,
                "type": notification.type,
                "message": notification.message,
                "read_status": notification.read_status,
                "timestamp": notification.timestamp
            }
            for notification in notifications
        ]
    }


# =========================================================
# MARK NOTIFICATION AS READ
# =========================================================

@router.post("/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.read_status = "read"

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification marked as read",
        "notification_id": notification.id,
        "read_status": notification.read_status
    }