from app.database.connection import Base

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Education(Base):
    __tablename__ = "educations"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    # =====================================================
    # Foreign Key → student_profiles.id
    # =====================================================

    student_profile_id = Column(
        BigInteger,
        ForeignKey(
            "student_profiles.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # Education Details
    # =====================================================

    institution = Column(
        String(200),
        nullable=False
    )

    degree = Column(
        String(150),
        nullable=False
    )

    field_of_study = Column(
        String(200),
        nullable=True
    )

    # Store year values such as "2025"
    start_date = Column(
        String(10),
        nullable=True
    )

    # Store year values such as "2029"
    end_date = Column(
        String(10),
        nullable=True
    )

    is_current = Column(
        Boolean,
        nullable=False,
        default=False
    )

    grade = Column(
        String(50),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # Timestamps
    # =====================================================

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # =====================================================
    # Relationship → StudentProfile
    # =====================================================

    student_profile = relationship(
        "StudentProfile",
        back_populates="educations"
    )

    # =====================================================
    # Relationship → EducationVerification
    # =====================================================

    verification = relationship(
        "EducationVerification",
        back_populates="education",
        uselist=False,
        cascade="all, delete-orphan"
    )