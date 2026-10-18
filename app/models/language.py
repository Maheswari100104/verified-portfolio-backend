from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    student_profile_id = Column(
        Integer,
        ForeignKey(
            "student_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    language = Column(
        String(100),
        nullable=False,
    )

    proficiency = Column(
        String(50),
        nullable=False,
    )

    # Relationship to StudentProfile
    student_profile = relationship(
        "StudentProfile",
        back_populates="languages",
    )