from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.language import Language
from app.models.student_profile import StudentProfile
from app.models.user import User

from app.schemas.language import (
    LanguageCreate,
    LanguageUpdate,
    LanguageResponse,
)

from app.core.dependencies import get_current_user


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/languages",
    tags=["Languages"],
)


# =========================================================
# Helper
# =========================================================

def get_student_profile(
    current_user: User,
    db: Session,
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can manage languages",
        )

    # -----------------------------------------------------
    # Find student profile
    # -----------------------------------------------------

    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == current_user.id
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    return profile


# =========================================================
# GET MY LANGUAGES
# =========================================================
#
# GET /languages/me
#
# =========================================================

@router.get(
    "/me",
    response_model=list[LanguageResponse],
)
def get_my_languages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(
        current_user,
        db,
    )

    return (
        db.query(Language)
        .filter(
            Language.student_profile_id == profile.id
        )
        .order_by(Language.id)
        .all()
    )


# =========================================================
# GET SINGLE LANGUAGE
# =========================================================
#
# GET /languages/{language_id}
#
# =========================================================

@router.get(
    "/{language_id}",
    response_model=LanguageResponse,
)
def get_language(
    language_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(
        current_user,
        db,
    )

    language = (
        db.query(Language)
        .filter(
            Language.id == language_id,
            Language.student_profile_id == profile.id,
        )
        .first()
    )

    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )

    return language


# =========================================================
# CREATE LANGUAGE
# =========================================================
#
# POST /languages
#
# =========================================================

@router.post(
    "",
    response_model=LanguageResponse,
    status_code=201,
)
def create_language(
    data: LanguageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Security check
    # -----------------------------------------------------

    if data.student_profile_id != profile.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create a language for another student",
        )

    # -----------------------------------------------------
    # Validate language
    # -----------------------------------------------------

    language_name = data.language.strip()

    if not language_name:
        raise HTTPException(
            status_code=400,
            detail="Language is required",
        )

    # -----------------------------------------------------
    # Validate proficiency
    # -----------------------------------------------------

    proficiency = data.proficiency.strip()

    if not proficiency:
        raise HTTPException(
            status_code=400,
            detail="Proficiency is required",
        )

    # -----------------------------------------------------
    # Create language
    # -----------------------------------------------------

    language = Language(
        student_profile_id=profile.id,
        language=language_name,
        proficiency=proficiency,
    )

    db.add(language)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()
        db.refresh(language)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create language",
        )

    return language


# =========================================================
# UPDATE LANGUAGE
# =========================================================
#
# PUT /languages/{language_id}
#
# =========================================================

@router.put(
    "/{language_id}",
    response_model=LanguageResponse,
)
def update_language(
    language_id: int,
    data: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find language
    # -----------------------------------------------------

    language = (
        db.query(Language)
        .filter(
            Language.id == language_id,
            Language.student_profile_id == profile.id,
        )
        .first()
    )

    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )

    # -----------------------------------------------------
    # Get only provided fields
    # -----------------------------------------------------

    update_data = data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Validate language
    # -----------------------------------------------------

    if "language" in update_data:

        value = update_data["language"]

        if value is None or not value.strip():
            raise HTTPException(
                status_code=400,
                detail="Language cannot be empty",
            )

        update_data["language"] = value.strip()

    # -----------------------------------------------------
    # Validate proficiency
    # -----------------------------------------------------

    if "proficiency" in update_data:

        value = update_data["proficiency"]

        if value is None or not value.strip():
            raise HTTPException(
                status_code=400,
                detail="Proficiency cannot be empty",
            )

        update_data["proficiency"] = value.strip()

    # -----------------------------------------------------
    # Apply updates
    # -----------------------------------------------------

    for field, value in update_data.items():

        setattr(
            language,
            field,
            value,
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()
        db.refresh(language)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update language",
        )

    return language


# =========================================================
# DELETE LANGUAGE
# =========================================================
#
# DELETE /languages/{language_id}
#
# =========================================================

@router.delete(
    "/{language_id}"
)
def delete_language(
    language_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find language
    # -----------------------------------------------------

    language = (
        db.query(Language)
        .filter(
            Language.id == language_id,
            Language.student_profile_id == profile.id,
        )
        .first()
    )

    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    db.delete(language)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete language",
        )

    return {
        "message": "Language deleted successfully"
    }