from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database.connection import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # =====================================================
    # Portfolio Data
    # =====================================================

    personal = Column(
        Text,
        nullable=True,
    )

    education = Column(
        Text,
        nullable=True,
    )

    skills = Column(
        Text,
        nullable=True,
    )

    projects = Column(
        Text,
        nullable=True,
    )

    experience = Column(
        Text,
        nullable=True,
    )

    certificates = Column(
        Text,
        nullable=True,
    )

    achievements = Column(
        Text,
        nullable=True,
    )

    languages = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # Portfolio Settings
    # =====================================================

    portfolio_template = Column(
        String(100),
        nullable=False,
        default="minimal",
    )

    portfolio_destination = Column(
        String(100),
        nullable=True,
    )

    # =====================================================
    # Publishing
    # =====================================================

    is_published = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    public_slug = Column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    # =====================================================
        # Final Resume
    # =====================================================

    resume_summary = Column(
    Text,
    nullable=True,
    )

    resume_source_signature = Column(
    Text,
    nullable=True,
    )

    resume_saved_at = Column(
    String(100),
    nullable=True,
    )

    # =====================================================
    # Relationship
    # =====================================================

    user = relationship(
        "User",
        back_populates="portfolio",
    )