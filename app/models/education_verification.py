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


class EducationVerification(Base):
    __tablename__ = "education_verifications"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    # =====================================================
    # Foreign Key → educations.id
    # =====================================================

    education_id = Column(
        BigInteger,
        ForeignKey(
            "educations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    # =====================================================
    # Uploaded Document
    # =====================================================

    document = Column(
        LargeBinary,
        nullable=False
    )

    document_name = Column(
        String(255),
        nullable=False
    )

    document_type = Column(
        String(100),
        nullable=False
    )

    document_size = Column(
        BigInteger,
        nullable=True
    )

    # =====================================================
    # Duplicate Detection
    # =====================================================

    document_hash = Column(
        String(64),
        nullable=False,
        index=True
    )

    # =====================================================
    # OCR Result
    # =====================================================

    ocr_data = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # Verification Status
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    # =====================================================
    # Verification Details
    # =====================================================

    verification_message = Column(
        Text,
        nullable=True
    )

    checked_at = Column(
        DateTime(timezone=True),
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
    # Relationship with Education
    # =====================================================

    education = relationship(
        "Education",
        back_populates="verification"
    )