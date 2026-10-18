from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Email
    # =====================================================

    email = Column(
        String(255),
        unique=True,
        nullable=False,
    )

    # =====================================================
    # Password
    # =====================================================

    password_hash = Column(
        String(255),
        nullable=False,
    )

    # =====================================================
    # Role
    # =====================================================

    role = Column(
        String(30),
        nullable=False,
        default="student",
    )

    # =====================================================
    # Account Status
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

    # =====================================================
    # Student Profile
    # =====================================================

    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # =====================================================
    # Mentor Profile
    # =====================================================

    mentor_profile = relationship(
        "MentorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

   

    portfolio = relationship(
        "Portfolio",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

   