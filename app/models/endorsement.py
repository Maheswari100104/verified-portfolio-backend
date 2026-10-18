from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class Endorsement(Base):
    __tablename__ = "endorsements"

    id = Column(Integer, primary_key=True, index=True)

    # Student who requested the endorsement
    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    # Mentor who will review the request
    mentor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    # Type of item being endorsed
    # Example: skill / project
    item_type = Column(
        String(50),
        nullable=False,
    )

    # ID of the skill/project
    item_id = Column(
        Integer,
        nullable=False,
    )

    # Name shown in the UI
    item_name = Column(
        String(255),
        nullable=False,
    )

    # Student's optional message
    message = Column(
        Text,
        nullable=True,
    )

    # Mentor's response
    mentor_comment = Column(
        Text,
        nullable=True,
    )

    # pending / endorsed / rejected
    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Whether mentor has endorsed it
    is_endorsed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )