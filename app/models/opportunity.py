from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    # =====================================================
    # Primary Key
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # IT Professional / Mentor who posted the opportunity
    # =====================================================

    professional_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Opportunity Type
    #
    # job / internship
    # =====================================================

    type = Column(
        String(30),
        nullable=False,
    )

    # =====================================================
    # Basic Opportunity Details
    # =====================================================

    type = Column(String(30), nullable=False)
    title = Column(
        String(200),
        nullable=False,
    )

    company = Column(
        String(255),
        nullable=False,
    )

    company_website = Column(String(500), nullable=True)
    company_phone = Column(String(30), nullable=True)
    company_email = Column(String(255), nullable=True)

    company_website = Column(
        String(500),
        nullable=True,
    )

    company_phone = Column(
        String(30),
        nullable=True,
    )

    company_email = Column(
        String(255),
        nullable=True,
    )


    location = Column(
        String(150),
        nullable=True,
    )

    work_mode = Column(
        String(50),
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
    # Required Skills
    #
    # Stored as simple text for now.
    # Example:
    # Python, SQL, Power BI
    # =====================================================

    required_skills = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Experience
    # =====================================================

    experience = Column(
        String(100),
        nullable=True,
    )

    # =====================================================
    # Eligibility
    # =====================================================

    eligibility = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Internship Duration
    # =====================================================

    duration = Column(
        String(100),
        nullable=True,
    )

    # =====================================================
    # Application Deadline
    # =====================================================

    deadline = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # Status
    #
    # active  → visible to students
    # closed  → no longer accepting interest
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="active",
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
    # Relationship → User
    # =====================================================

    professional = relationship(
        "User",
        backref="opportunities",
    )

    # =====================================================
    # Relationship → Interested Students
    # =====================================================

    interests = relationship(
        "OpportunityInterest",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )