from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class ShortlistedCandidate(Base):
    __tablename__ = "shortlisted_candidates"

    id = Column(BigInteger, primary_key=True, index=True)

    professional_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    opportunity_id = Column(
        BigInteger,
        ForeignKey("opportunities.id"),
        nullable=False,
        index=True,
    )

    student_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status = Column(
        String,
        nullable=False,
        default="shortlisted",
    )

    shortlisted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "professional_id",
            "opportunity_id",
            "student_id",
            name="uq_shortlisted_candidate",
        ),
    )