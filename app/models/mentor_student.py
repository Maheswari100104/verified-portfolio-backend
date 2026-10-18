from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class MentorStudent(Base):
    __tablename__ = "mentor_students"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Mentor → users.id
    # =====================================================

    mentor_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # Student → users.id
    # =====================================================

    student_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # Relationship Status
    #
    # pending  → student requested mentor
    # accepted → mentor accepted
    # rejected → mentor rejected
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    # =====================================================
    # Active Relationship
    # =====================================================

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # =====================================================
    # Timestamps
    # =====================================================

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )