from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.experience import Experience
from app.models.student_profile import StudentProfile
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)


router = APIRouter(
    prefix="/student/experiences",
    tags=["Student - Experience"],
)


# ============================================================
# CREATE EXPERIENCE
# ============================================================

@router.post(
    "/{student_profile_id}",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_experience(
    student_profile_id: int,
    experience: ExperienceCreate,
    db: Session = Depends(get_db),
):
    # Check whether student profile exists
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.id == student_profile_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    # If currently working, there should be no end date
    if experience.is_current:
        experience.end_date = None

    new_experience = Experience(
        student_profile_id=student_profile_id,
        company=experience.company,
        position=experience.position,
        employment_type=experience.employment_type,
        location=experience.location,
        start_date=experience.start_date,
        end_date=experience.end_date,
        is_current=experience.is_current,
        description=experience.description,
    )

    db.add(new_experience)
    db.commit()
    db.refresh(new_experience)

    return new_experience


# ============================================================
# GET ALL EXPERIENCES
# ============================================================

@router.get(
    "/{student_profile_id}",
    response_model=list[ExperienceResponse],
)
def get_experiences(
    student_profile_id: int,
    db: Session = Depends(get_db),
):
    # Check student profile
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.id == student_profile_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    experiences = (
        db.query(Experience)
        .filter(
            Experience.student_profile_id
            == student_profile_id
        )
        .order_by(Experience.id.desc())
        .all()
    )

    return experiences


# ============================================================
# GET ONE EXPERIENCE
# ============================================================

@router.get(
    "/item/{experience_id}",
    response_model=ExperienceResponse,
)
def get_experience(
    experience_id: int,
    db: Session = Depends(get_db),
):
    experience = (
        db.query(Experience)
        .filter(Experience.id == experience_id)
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )

    return experience


# ============================================================
# UPDATE EXPERIENCE
# ============================================================

@router.put(
    "/item/{experience_id}",
    response_model=ExperienceResponse,
)
def update_experience(
    experience_id: int,
    experience_data: ExperienceUpdate,
    db: Session = Depends(get_db),
):
    experience = (
        db.query(Experience)
        .filter(Experience.id == experience_id)
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )

    update_data = experience_data.model_dump(
        exclude_unset=True
    )

    # If currently working, remove end date
    if update_data.get("is_current") is True:
        update_data["end_date"] = None

    for field, value in update_data.items():
        setattr(experience, field, value)

    db.commit()
    db.refresh(experience)

    return experience


# ============================================================
# DELETE EXPERIENCE
# ============================================================

@router.delete(
    "/item/{experience_id}",
)
def delete_experience(
    experience_id: int,
    db: Session = Depends(get_db),
):
    experience = (
        db.query(Experience)
        .filter(Experience.id == experience_id)
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )

    db.delete(experience)
    db.commit()

    return {
        "message": "Experience deleted successfully"
    }