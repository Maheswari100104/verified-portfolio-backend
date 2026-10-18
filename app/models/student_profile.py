from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    # =====================================================
    # Foreign Key → users.id
    # =====================================================

    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    # =====================================================
    # Basic Details
    # =====================================================

    full_name = Column(
        String(150),
        nullable=False
    )

    phone = Column(
        String(20),
        nullable=True
    )

    location = Column(
        String(150),
        nullable=True
    )

    headline = Column(
        String(255),
        nullable=True
    )

    # =====================================================
    # Social Links
    # =====================================================

    linkedin = Column(
        String(500),
        nullable=True
    )

    github = Column(
        String(500),
        nullable=True
    )

    website = Column(
        String(500),
        nullable=True
    )

    # =====================================================
    # About Me
    # =====================================================

    about = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # Profile Photo
    # =====================================================

    profile_photo = Column(
        LargeBinary,
        nullable=True
    )

    profile_photo_name = Column(
        String(255),
        nullable=True
    )

    profile_photo_type = Column(
        String(100),
        nullable=True
    )

    profile_photo_size = Column(
        BigInteger,
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
    # Relationship with User
    # =====================================================

    user = relationship(
        "User",
        back_populates="student_profile"
    )

    # =====================================================
    # Relationship with Experience
    # =====================================================

    experiences = relationship(
        "Experience",
        back_populates="student_profile",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # Relationship with Education
    # =====================================================

    educations = relationship(
        "Education",
        back_populates="student_profile",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # Relationship with StudentSkill
    # =====================================================

    student_skills = relationship(
        "StudentSkill",
        back_populates="student_profile",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # Relationship with Project
    # =====================================================

    projects = relationship(
        "Project",
        back_populates="student_profile",
        cascade="all, delete-orphan"
    )

    certificates = relationship(
    "Certificate",
    back_populates="student_profile",
    cascade="all, delete-orphan",
)
    achievements = relationship(
    "Achievement",
    back_populates="student_profile",
    cascade="all, delete-orphan",
)

    languages = relationship(
    "Language",
    back_populates="student_profile",
    cascade="all, delete-orphan",
)