from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    DateTime,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Foreign Key → users.id
    # =====================================================

    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    # =====================================================
    # Basic Details
    # =====================================================

    full_name = Column(
        String(150),
        nullable=False,
    )

    phone = Column(
        String(20),
        nullable=True,
    )

    # =====================================================
    # Mentor Type
    # teacher / trainer
    # =====================================================

    mentor_type = Column(
        String(30),
        nullable=False,
        default="teacher",
    )

    # =====================================================
    # Professional Details
    # =====================================================

    institution = Column(
        String(255),
        nullable=True,
    )

    institution_email = Column(
        String(255),
        nullable=True,
    )

    department = Column(
        String(200),
        nullable=True,
    )

    designation = Column(
        String(150),
        nullable=True,
    )

    specialization = Column(
        String(255),
        nullable=True,
    )

    location = Column(
        String(150),
        nullable=True,
    )

    # =====================================================
    # About
    # =====================================================

    about = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Profile Photo
    # =====================================================

    profile_photo = Column(
        LargeBinary,
        nullable=True,
    )

    profile_photo_name = Column(
        String(255),
        nullable=True,
    )

    profile_photo_type = Column(
        String(100),
        nullable=True,
    )

    profile_photo_size = Column(
        BigInteger,
        nullable=True,
    )

    # =====================================================
    # Verification Document
    # =====================================================

    verification_document = Column(
        LargeBinary,
        nullable=True,
    )

    verification_document_name = Column(
        String(255),
        nullable=True,
    )

    verification_document_type = Column(
        String(100),
        nullable=True,
    )

    verification_document_size = Column(
        BigInteger,
        nullable=True,
    )

    # =====================================================
    # Verification Status
    #
    # pending  → waiting for verification
    # verified → approved mentor
    # rejected → verification rejected
    # =====================================================

    verification_status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    # =====================================================
    # OCR Extracted Text
    # =====================================================

    ocr_extracted_text = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # AI Verification
    # =====================================================

    ai_verification_score = Column(
        Float,
        nullable=True,
    )

    ai_verification_result = Column(
        Text,
        nullable=True,
    )

    ai_verified = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # =====================================================
    # Final Verification
    # =====================================================

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_by = Column(
        BigInteger,
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
    )

    # =====================================================
    # Relationship with User
    # =====================================================

    user = relationship(
        "User",
        back_populates="mentor_profile",
    )