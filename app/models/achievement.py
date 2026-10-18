from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
    Text,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Achievement(Base):
    __tablename__ = "achievements"

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
        index=True,
    )

    # =====================================================
    # Achievement Information
    # =====================================================

    title = Column(
        String(200),
        nullable=False,
    )

    organization = Column(
        String(200),
        nullable=False,
    )

    # =====================================================
    # Achievement Date
    # =====================================================
    #
    # Frontend uses <input type="month">
    #
    # Example:
    # "2026-08"
    #
    # Stored as String so we don't get the
    # "valid date or datetime" validation problem.
    #
    # =====================================================

    achievement_date = Column(
        String(7),
        nullable=True,
    )

    # =====================================================
    # Category
    # =====================================================

    category = Column(
        String(100),
        nullable=True,
    )

    # =====================================================
    # Description
    # =====================================================

    description = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Certificate / Proof URL
    # =====================================================

    certificate_url = Column(
        String(500),
        nullable=True,
    )

    # =====================================================
    # Uploaded Proof File
    # =====================================================
    #
    # PDF / JPG / PNG
    #
    # Maximum file size will be validated
    # in the router.
    #
    # =====================================================

    certificate_file = Column(
        LargeBinary,
        nullable=True,
    )

    certificate_file_name = Column(
        String(255),
        nullable=True,
    )

    certificate_file_type = Column(
        String(100),
        nullable=True,
    )

    certificate_file_size = Column(
        BigInteger,
        nullable=True,
    )

    # =====================================================
    # Relationship with StudentProfile
    # =====================================================

    student_profile = relationship(
        "StudentProfile",
        back_populates="achievements",
    )