from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
    Text,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Project(Base):
    __tablename__ = "projects"

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
        nullable=False,
        index=True
    )

    # =====================================================
    # Project Information
    # =====================================================

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    # =====================================================
    # Technologies
    # =====================================================

    technologies = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # Project Links
    # =====================================================

    github = Column(
        String(500),
        nullable=True
    )

    live_demo = Column(
        String(500),
        nullable=True
    )

    # =====================================================
    # Project Image
    # =====================================================

    image = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # Project Dates
    # =====================================================

    start_date = Column(
        Date,
        nullable=True
    )

    end_date = Column(
        Date,
        nullable=True
    )

    # =====================================================
    # Currently Working
    # =====================================================

    is_current = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # =====================================================
    # Relationship with StudentProfile
    # =====================================================

    student_profile = relationship(
        "StudentProfile",
        back_populates="projects"
    )

    # =====================================================
    # Project Verification
    #
    # One project can have multiple verification records.
    #
    # Example:
    #
    # Project
    #    ├── Verification #1 → rejected
    #    ├── Verification #2 → pending
    #    └── Verification #3 → verified
    #
    # =====================================================

    verifications = relationship(
        "ProjectVerification",
        back_populates="project",
        cascade="all, delete-orphan",
    )