from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class ExperienceVerification(Base):
    __tablename__ = "experience_verifications"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Experience → experiences.id
    # =====================================================

    experience_id = Column(
        BigInteger,
        ForeignKey(
            "experiences.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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
        index=True,
    )

    # =====================================================
    # IT Professional → users.id
    #
    # This can represent:
    # - Recruiter
    # - HR Professional
    # - Industry Professional
    # - Mentor
    #
    # We keep the database field as mentor_id for now
    # because the existing project uses that name.
    # =====================================================

    mentor_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # =====================================================
    # Verification Status
    #
    # pending
    # verified
    # rejected
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # =====================================================
    # Professional Rating
    #
    # 1 → Very Poor
    # 2 → Needs Improvement
    # 3 → Average
    # 4 → Good
    # 5 → Excellent
    # =====================================================

    rating = Column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # Professional Feedback
    # =====================================================

    feedback = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Student Message
    # =====================================================

    comment = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Verification Flag
    # =====================================================

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # =====================================================
    # Verified At
    # =====================================================

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
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
        onupdate=func.now(),
    )

    # =====================================================
    # Relationship → Experience
    # =====================================================

    experience = relationship(
        "Experience",
        back_populates="verifications",
    )

    # =====================================================
    # Relationship → Student
    # =====================================================

    student = relationship(
        "User",
        foreign_keys=[student_id],
    )

    # =====================================================
    # Relationship → IT Professional
    # =====================================================

    mentor = relationship(
        "User",
        foreign_keys=[mentor_id],
    )