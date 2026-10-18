from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.education import Education
from app.schemas.education import (
    EducationCreate,
    EducationUpdate,
    EducationResponse,
)


router = APIRouter(
    prefix="/student/education",
    tags=["Student Education"],
)


# =========================================================
# CREATE EDUCATION
# =========================================================

@router.post(
    "/{student_profile_id}",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_education(
    student_profile_id: int,
    education: EducationCreate,
    db: Session = Depends(get_db),
):
    new_education = Education(
        student_profile_id=student_profile_id,
        institution=education.institution,
        degree=education.degree,
        field_of_study=education.field_of_study,
        start_date=education.start_date,
        end_date=education.end_date,
        is_current=education.is_current,
        grade=education.grade,
        description=education.description,
    )

    db.add(new_education)
    db.commit()
    db.refresh(new_education)

    return new_education


# =========================================================
# GET ALL EDUCATION
# =========================================================

@router.get(
    "/{student_profile_id}",
    response_model=list[EducationResponse],
)
def get_education(
    student_profile_id: int,
    db: Session = Depends(get_db),
):
    education_list = (
        db.query(Education)
        .options(
            joinedload(Education.verification)
        )
        .filter(
            Education.student_profile_id
            == student_profile_id
        )
        .order_by(
            Education.start_date.desc()
        )
        .all()
    )

    return education_list


# =========================================================
# GET SINGLE EDUCATION
# =========================================================

@router.get(
    "/item/{education_id}",
    response_model=EducationResponse,
)
def get_single_education(
    education_id: int,
    db: Session = Depends(get_db),
):
    education = (
        db.query(Education)
        .options(
            joinedload(Education.verification)
        )
        .filter(
            Education.id == education_id
        )
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education not found",
        )

    return education


# =========================================================
# UPDATE EDUCATION
# =========================================================

@router.put(
    "/item/{education_id}",
    response_model=EducationResponse,
)
def update_education(
    education_id: int,
    education_data: EducationUpdate,
    db: Session = Depends(get_db),
):
    education = (
        db.query(Education)
        .filter(
            Education.id == education_id
        )
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education not found",
        )

    update_data = education_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            education,
            field,
            value
        )

    db.commit()
    db.refresh(education)

    return education


# =========================================================
# DELETE EDUCATION
# =========================================================

@router.delete(
    "/item/{education_id}"
)
def delete_education(
    education_id: int,
    db: Session = Depends(get_db),
):
    education = (
        db.query(Education)
        .filter(
            Education.id == education_id
        )
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education not found",
        )

    db.delete(education)
    db.commit()

    return {
        "message": "Education deleted successfully"
    }