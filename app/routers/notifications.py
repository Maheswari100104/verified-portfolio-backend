
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


# =========================================================
# NOTIFICATION RECIPIENT FILTER
# =========================================================

def recipient_filter(current_user: User):
    """
    Return notifications belonging to the authenticated user.

    New notifications:
        recipient_id identifies the actual recipient.

    Legacy student notifications:
        Older records may have recipient_id=NULL and use
        student_id to identify the student recipient.

    Legacy fallback is restricted to student accounts.
    """

    user_role = getattr(current_user.role, "value", current_user.role)

    # New notifications addressed to this user.
    recipient_condition = (
        Notification.recipient_id == current_user.id
    )

    # Preserve compatibility with existing student notifications.
    if user_role == "student":
        legacy_student_condition = (
            Notification.recipient_id.is_(None)
            & (Notification.student_id == current_user.id)
        )

        return or_(
            recipient_condition,
            legacy_student_condition,
        )

    # Mentors and other roles can only see notifications
    # explicitly addressed to their user ID.
    return recipient_condition


# =========================================================
# SERIALIZE NOTIFICATION
# =========================================================

def serialize_notification(notification: Notification):
    return {
        "id": notification.id,
        "student_id": notification.student_id,
        "recipient_id": notification.recipient_id,
        "sender_id": notification.sender_id,
        "opportunity_id": notification.opportunity_id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }


# =========================================================
# GET MY NOTIFICATIONS
# GET /notifications/
# =========================================================

@router.get("/")
def get_my_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(
        recipient_filter(current_user)
    )

    if unread_only:
        query = query.filter(
            Notification.is_read.is_(False)
        )

    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [
        serialize_notification(notification)
        for notification in notifications
    ]


# =========================================================
# GET UNREAD NOTIFICATION COUNT
# GET /notifications/unread-count
# =========================================================

@router.get("/unread-count")
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(
            recipient_filter(current_user),
            Notification.is_read.is_(False),
        )
        .count()
    )

    return {
        "unread_count": count,
    }


# =========================================================
# MARK ONE NOTIFICATION AS READ
# PUT /notifications/{notification_id}/read
# =========================================================

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            recipient_filter(current_user),
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    try:
        notification.is_read = True
        db.commit()
        db.refresh(notification)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )

    return {
        "message": "Notification marked as read",
        "notification_id": notification.id,
        "is_read": notification.is_read,
    }


# =========================================================
# MARK ALL NOTIFICATIONS AS READ
# PUT /notifications/read-all
# =========================================================

@router.put("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated_count = (
            db.query(Notification)
            .filter(
                recipient_filter(current_user),
                Notification.is_read.is_(False),
            )
            .update(
                {Notification.is_read: True},
                synchronize_session=False,
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read",
        )

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count,
    }
