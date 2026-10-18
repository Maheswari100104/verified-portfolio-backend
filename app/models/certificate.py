from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
    Text,
    Date,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Certificate(Base):
    __tablename__ = "certificates"

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
    # Certificate Information
    # =====================================================

    title = Column(
        String(200),
        nullable=False,
    )

    issuer = Column(
        String(200),
        nullable=False,
    )

    # =====================================================
    # Certificate Dates
    # =====================================================

    issue_date = Column(
        Date,
        nullable=True,
    )

    expiry_date = Column(
        Date,
        nullable=True,
    )

    # =====================================================
    # Credential Information
    # =====================================================

    credential_id = Column(
        String(200),
        nullable=True,
    )

    credential_url = Column(
        String(500),
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
    # Certificate Image
    # =====================================================

    image = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Certificate PDF
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
        back_populates="certificates",
    )