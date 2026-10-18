from sqlalchemy import BigInteger, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id"),
        nullable=False
    )

    skill_id = Column(
        Integer,
        ForeignKey("skills.id"),
        nullable=True
    )

    custom_skill_name = Column(
        String(100),
        nullable=True
    )

    # Skill proficiency level
    level = Column(
        String(20),
        nullable=False,
        default="Intermediate",
        server_default="Intermediate"
    )

    # Relationship with StudentProfile
    student_profile = relationship(
        "StudentProfile",
        back_populates="student_skills"
    )

    # Relationship with Skill
    skill = relationship(
        "Skill",
        back_populates="student_skills"
    )