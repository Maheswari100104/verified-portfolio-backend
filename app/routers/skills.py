from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.skill import Skill
from app.models.student_skill import StudentSkill

from app.schemas.skills import (
    SkillResponse,
    StudentSkillCreate,
    StudentSkillUpdate,
    StudentSkillResponse,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)


# =========================================================
# Database Dependency
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# GET ALL AVAILABLE SKILLS
# =========================================================

@router.get(
    "/",
    response_model=list[SkillResponse]
)
def get_skills(
    db: Session = Depends(get_db)
):
    return (
        db.query(Skill)
        .order_by(
            Skill.category,
            Skill.name
        )
        .all()
    )


# =========================================================
# ADD SKILL TO STUDENT
# =========================================================

@router.post(
    "/student",
    response_model=StudentSkillResponse,
    status_code=201
)
def add_student_skill(
    data: StudentSkillCreate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # Validate skill input
    # =====================================================

    if (
        not data.skill_id
        and not data.custom_skill_name
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Either skill_id or "
                "custom_skill_name is required"
            )
        )

    if (
        data.skill_id
        and data.custom_skill_name
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide either skill_id "
                "or custom_skill_name, not both"
            )
        )

    # =====================================================
    # Validate level
    # =====================================================

    allowed_levels = {
        "Beginner",
        "Intermediate",
        "Advanced",
        "Expert",
    }

    if data.level not in allowed_levels:
        raise HTTPException(
            status_code=400,
            detail="Invalid skill level"
        )

    # =====================================================
    # Validate predefined skill
    # =====================================================

    if data.skill_id:

        skill = (
            db.query(Skill)
            .filter(
                Skill.id == data.skill_id
            )
            .first()
        )

        if not skill:
            raise HTTPException(
                status_code=404,
                detail="Skill not found"
            )

    # =====================================================
    # Validate custom skill
    # =====================================================

    if data.custom_skill_name:

        custom_name = (
            data.custom_skill_name.strip()
        )

        if not custom_name:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Custom skill name "
                    "cannot be empty"
                )
            )

        data.custom_skill_name = custom_name

    # =====================================================
    # Check duplicate
    # =====================================================

    if data.skill_id:

        existing = (
            db.query(StudentSkill)
            .filter(
                StudentSkill.student_profile_id
                == data.student_profile_id,

                StudentSkill.skill_id
                == data.skill_id
            )
            .first()
        )

    else:

        existing = (
            db.query(StudentSkill)
            .filter(
                StudentSkill.student_profile_id
                == data.student_profile_id,

                StudentSkill.custom_skill_name.ilike(
                    data.custom_skill_name
                )
            )
            .first()
        )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Skill already added"
        )

    # =====================================================
    # Create StudentSkill
    # =====================================================

    student_skill = StudentSkill(
        student_profile_id=data.student_profile_id,

        skill_id=data.skill_id,

        custom_skill_name=data.custom_skill_name,

        # IMPORTANT
        # Save selected proficiency level
        level=data.level,
    )

    db.add(student_skill)

    db.commit()

    db.refresh(student_skill)

    return student_skill


# =========================================================
# GET STUDENT SKILLS
# =========================================================

@router.get(
    "/student/{student_profile_id}",
    response_model=list[StudentSkillResponse]
)
def get_student_skills(
    student_profile_id: int,
    db: Session = Depends(get_db)
):

    return (
        db.query(StudentSkill)
        .filter(
            StudentSkill.student_profile_id
            == student_profile_id
        )
        .order_by(
            StudentSkill.id
        )
        .all()
    )


# =========================================================
# UPDATE STUDENT SKILL
# =========================================================

@router.put(
    "/student/{student_skill_id}",
    response_model=StudentSkillResponse
)
def update_student_skill(
    student_skill_id: int,
    data: StudentSkillUpdate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # Find student skill
    # =====================================================

    student_skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.id
            == student_skill_id
        )
        .first()
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student skill not found"
        )

    # =====================================================
    # Update level
    # =====================================================

    if data.level is not None:
        student_skill.level = data.level

    # =====================================================
    # Save
    # =====================================================

    db.commit()

    db.refresh(student_skill)

    return student_skill


# =========================================================
# DELETE STUDENT SKILL
# =========================================================

@router.delete(
    "/student/{student_skill_id}"
)
def delete_student_skill(
    student_skill_id: int,
    db: Session = Depends(get_db)
):

    # =====================================================
    # Find student skill
    # =====================================================

    student_skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.id
            == student_skill_id
        )
        .first()
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student skill not found"
        )

    # =====================================================
    # Delete
    # =====================================================

    db.delete(student_skill)

    db.commit()

    return {
        "message": "Skill removed successfully"
    }