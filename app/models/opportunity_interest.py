from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class OpportunityInterest(Base):
    __tablename__ = "opportunity_interests"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # Opportunity
    # =====================================================

    opportunity_id = Column(
        BigInteger,
        ForeignKey(
            "opportunities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Student
    # =====================================================

    student_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Interest Status
    #
    # interested → student showed interest
    # shortlisted → recruiter shortlisted
    # rejected → recruiter rejected
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="interested",
    )

    # =====================================================
    # AI Match Percentage
    #
    # Will be filled when we implement AI matching.
    # Example: 92.5
    # =====================================================

    ai_match_percentage = Column(
        String(10),
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
    # Relationships
    # =====================================================

    opportunity = relationship(
        "Opportunity",
        back_populates="interests",
    )

    student = relationship(
        "User",
        foreign_keys=[student_id],
    )

    # =====================================================
    # Prevent duplicate interest
    #
    # One student can show interest only once
    # for the same opportunity.
    # =====================================================

    __table_args__ = (
        UniqueConstraint(
            "opportunity_id",
            "student_id",
            name="uq_opportunity_student_interest",
        ),
    )