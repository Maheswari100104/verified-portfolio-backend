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


class ProjectVerification(Base):
    __tablename__ = "project_verifications"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =========================================================
    # Project being verified
    # =========================================================
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # =========================================================
    # Student who owns the project
    # =========================================================
    student_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # =========================================================
    # Mentor / IT Professional reviewing the project
    # =========================================================
    mentor_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # =========================================================
    # Verification status
    #
    # pending  -> Waiting for mentor review
    # verified -> Mentor approved the project
    # rejected -> Mentor rejected the project
    #
    # If no record exists, the student has not submitted
    # a verification request.
    # =========================================================
    status = Column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # =========================================================
    # Mentor rating
    # Example: 1 to 5
    # =========================================================
    rating = Column(
        Integer,
        nullable=True,
    )

    # =========================================================
    # Mentor feedback
    # =========================================================
    feedback = Column(
        Text,
        nullable=True,
    )

    # =========================================================
    # Additional mentor comment
    # =========================================================
    comment = Column(
        Text,
        nullable=True,
    )

    # =========================================================
    # Verification flag
    # =========================================================
    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # =========================================================
    # When mentor verified the project
    # =========================================================
    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =========================================================
    # Timestamps
    # =========================================================
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

    # =========================================================
    # Relationships
    # =========================================================

    project = relationship(
        "Project",
        back_populates="verifications",
    )

    student = relationship(
        "User",
        foreign_keys=[student_id],
    )

    mentor = relationship(
        "User",
        foreign_keys=[mentor_id],
    )