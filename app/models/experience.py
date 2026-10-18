from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Experience(Base):
    __tablename__ = "experiences"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Foreign Key → student_profiles.id
    # =====================================================

    student_profile_id = Column(
        BigInteger,
        ForeignKey(
            "student_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # Experience Details
    # =====================================================

    company = Column(
        String(200),
        nullable=False,
    )

    position = Column(
        String(200),
        nullable=False,
    )

    employment_type = Column(
        String(50),
        nullable=True,
    )

    location = Column(
        String(200),
        nullable=True,
    )

    start_date = Column(
        Date,
        nullable=True,
    )

    end_date = Column(
        Date,
        nullable=True,
    )

    is_current = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    description = Column(
        Text,
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
    # Relationship → StudentProfile
    # =====================================================

    student_profile = relationship(
        "StudentProfile",
        back_populates="experiences",
    )

    # =====================================================
    # Relationship → ExperienceVerification
    # =====================================================

    verifications = relationship(
        "ExperienceVerification",
        back_populates="experience",
        cascade="all, delete-orphan",
    )