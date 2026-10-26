
from datetime import date
from typing import Optional

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
# HELPER: CONVERT MONTH OR DATE STRINGS TO PYTHON DATE OBJECTS
# ============================================================

def parse_experience_date(value) -> Optional[date]:
    """
    Converts incoming date values into Python date objects.

    Accepted values:
        None          -> None
        ""            -> None
        "2026-05"     -> date(2026, 5, 1)
        "2026-05-15"  -> date(2026, 5, 15)

    HTML month inputs send dates in YYYY-MM format.
    PostgreSQL DATE columns require complete dates.
    """

    if value is None:
        return None

    if isinstance(value, date):
        return value

    value = str(value).strip()

    if not value:
        return None

    try:
        if len(value) == 7:
            return date.fromisoformat(f"{value}-01")

        return date.fromisoformat(value)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid experience date '{value}'. "
                "Use YYYY-MM or YYYY-MM-DD."
            ),
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
    # Check whether the student profile exists.
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.id == student_profile_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    # Convert frontend date strings before saving.
    start_date = parse_experience_date(
        experience.start_date
    )

    # Current employment must not have an end date.
    end_date = (
        None
        if experience.is_current
        else parse_experience_date(experience.end_date)
    )

    new_experience = Experience(
        student_profile_id=student_profile_id,
        company=experience.company,
        position=experience.position,
        employment_type=experience.employment_type,
        location=experience.location,
        start_date=start_date,
        end_date=end_date,
        is_current=experience.is_current,
        description=experience.description,
    )

    try:
        db.add(new_experience)
        db.commit()
        db.refresh(new_experience)

    except Exception:
        db.rollback()
        raise

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
    # Check whether the student profile exists.
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.id == student_profile_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    experiences = (
        db.query(Experience)
        .filter(
            Experience.student_profile_id == student_profile_id
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
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    # Get only the fields supplied by the frontend.
    update_data = experience_data.model_dump(
        exclude_unset=True
    )

    # Convert the start date if supplied.
    if "start_date" in update_data:
        update_data["start_date"] = parse_experience_date(
            update_data["start_date"]
        )

    # Convert the end date if supplied.
    if "end_date" in update_data:
        update_data["end_date"] = parse_experience_date(
            update_data["end_date"]
        )

    # If currently working, always clear the end date.
    if update_data.get("is_current") is True:
        update_data["end_date"] = None

    # Apply the updated fields.
    for field, value in update_data.items():
        setattr(experience, field, value)

    try:
        db.commit()
        db.refresh(experience)

    except Exception:
        db.rollback()
        raise

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    try:
        db.delete(experience)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Experience deleted successfully"
    }
