
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # Legacy student recipient; retained for compatibility
    student_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Actual recipient for new student or mentor notifications
    recipient_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # User who triggered the notification
    sender_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Related opportunity, when applicable
    opportunity_id = Column(
        BigInteger,
        ForeignKey("opportunities.id"),
        nullable=True,
        index=True,
    )

    # Examples: feedback_request, opportunity_interest, shortlist
    type = Column(
        String,
        nullable=False,
        default="general",
    )

    title = Column(
        String,
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
