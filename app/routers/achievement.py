from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)

from fastapi.responses import Response

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.achievement import Achievement
from app.models.student_profile import StudentProfile
from app.models.user import User

from app.schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
)

from app.core.dependencies import get_current_user


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/achievements",
    tags=["Achievements"],
)


# =========================================================
# Constants
# =========================================================

MAX_FILE_SIZE = 10 * 1024 * 1024


# =========================================================
# Allowed File Types
# =========================================================

ALLOWED_FILE_TYPES = {
    # PDF
    "application/pdf",

    # Images
    "image/jpeg",
    "image/png",
    "image/webp",

    # Microsoft Word
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

    # Microsoft PowerPoint
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    # Microsoft Excel
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    # Text
    "text/plain",
}


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
            detail="Only students can manage achievements",
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
# Achievement Response Helper
# =========================================================
#
# IMPORTANT:
#
# The URL returned here is the PUBLIC file URL.
#
# Public portfolio:
# /achievements/public/{achievement_id}/file
#
# =========================================================

def build_achievement_response(
    achievement: Achievement,
) -> AchievementResponse:

    response = AchievementResponse.model_validate(
        achievement
    )

    if achievement.certificate_file:

        response.certificate_file_url = (
            f"/achievements/public/"
            f"{achievement.id}/file"
        )

    else:

        response.certificate_file_url = None

    return response


# =========================================================
# Validate Achievement Date
# =========================================================

def validate_achievement_date(
    value: str | None,
):

    if value is None or value == "":
        return None

    if len(value) != 7:
        raise HTTPException(
            status_code=400,
            detail="Achievement date must be in YYYY-MM format",
        )

    if value[4] != "-":
        raise HTTPException(
            status_code=400,
            detail="Achievement date must be in YYYY-MM format",
        )

    year = value[:4]
    month = value[5:]

    if not year.isdigit() or not month.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Achievement date must be in YYYY-MM format",
        )

    month_number = int(month)

    if month_number < 1 or month_number > 12:
        raise HTTPException(
            status_code=400,
            detail="Achievement month must be between 01 and 12",
        )

    return value


# =========================================================
# GET MY ACHIEVEMENTS
# =========================================================
#
# GET /achievements/me
#
# Requires authentication.
#
# =========================================================

@router.get(
    "/me",
    response_model=list[AchievementResponse],
)
def get_my_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    achievements = (
        db.query(Achievement)
        .filter(
            Achievement.student_profile_id
            == profile.id
        )
        .order_by(Achievement.id)
        .all()
    )

    return [
        build_achievement_response(
            achievement
        )
        for achievement in achievements
    ]


# =========================================================
# PUBLIC GET ACHIEVEMENT FILE
# =========================================================
#
# GET /achievements/public/{achievement_id}/file
#
# NO AUTHENTICATION REQUIRED.
#
# This endpoint is used by the published portfolio.
#
# IMPORTANT:
# This route is intentionally placed BEFORE:
#
#     /{achievement_id}
#
# =========================================================

@router.get(
    "/public/{achievement_id}/file"
)
def get_public_achievement_file(
    achievement_id: int,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # Find achievement
    # -----------------------------------------------------

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Check uploaded file
    # -----------------------------------------------------

    if not achievement.certificate_file:

        raise HTTPException(
            status_code=404,
            detail="Achievement proof file not found",
        )

    # -----------------------------------------------------
    # Return file
    # -----------------------------------------------------

    return Response(
        content=achievement.certificate_file,
        media_type=(
            achievement.certificate_file_type
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition": (
                f'inline; filename="{achievement.certificate_file_name}"'
            )
        },
    )


# =========================================================
# GET SINGLE ACHIEVEMENT
# =========================================================
#
# GET /achievements/{achievement_id}
#
# Requires authentication.
#
# =========================================================

@router.get(
    "/{achievement_id}",
    response_model=AchievementResponse,
)
def get_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    return build_achievement_response(
        achievement
    )


# =========================================================
# CREATE ACHIEVEMENT
# =========================================================
#
# POST /achievements
#
# =========================================================

@router.post(
    "",
    response_model=AchievementResponse,
    status_code=201,
)
def create_achievement(
    data: AchievementCreate,
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
            detail=(
                "You cannot create an achievement "
                "for another student"
            ),
        )

    # -----------------------------------------------------
    # Validate title
    # -----------------------------------------------------

    title = data.title.strip()

    if not title:

        raise HTTPException(
            status_code=400,
            detail="Achievement title is required",
        )

    # -----------------------------------------------------
    # Validate organization
    # -----------------------------------------------------

    organization = data.organization.strip()

    if not organization:

        raise HTTPException(
            status_code=400,
            detail="Organization is required",
        )

    # -----------------------------------------------------
    # Validate date
    # -----------------------------------------------------

    achievement_date = (
        validate_achievement_date(
            data.achievement_date
        )
    )

    # -----------------------------------------------------
    # Optional fields
    # -----------------------------------------------------

    category = (
        data.category.strip()
        if data.category
        else None
    )

    description = (
        data.description.strip()
        if data.description
        else None
    )

    certificate_url = (
        data.certificate_url.strip()
        if data.certificate_url
        else None
    )

    # -----------------------------------------------------
    # Create achievement
    # -----------------------------------------------------

    achievement = Achievement(
        student_profile_id=profile.id,

        title=title,

        organization=organization,

        achievement_date=achievement_date,

        category=category,

        description=description,

        certificate_url=certificate_url,
    )

    db.add(achievement)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(achievement)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create achievement",
        )

    return build_achievement_response(
        achievement
    )


# =========================================================
# UPDATE ACHIEVEMENT
# =========================================================
#
# PUT /achievements/{achievement_id}
#
# =========================================================

@router.put(
    "/{achievement_id}",
    response_model=AchievementResponse,
)
def update_achievement(
    achievement_id: int,
    data: AchievementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find achievement
    # -----------------------------------------------------

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Get provided fields
    # -----------------------------------------------------

    update_data = data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Validate title
    # -----------------------------------------------------

    if "title" in update_data:

        value = update_data["title"]

        if value is None or not value.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "Achievement title "
                    "cannot be empty"
                ),
            )

        update_data["title"] = value.strip()

    # -----------------------------------------------------
    # Validate organization
    # -----------------------------------------------------

    if "organization" in update_data:

        value = update_data["organization"]

        if value is None or not value.strip():

            raise HTTPException(
                status_code=400,
                detail="Organization cannot be empty",
            )

        update_data["organization"] = value.strip()

    # -----------------------------------------------------
    # Validate date
    # -----------------------------------------------------

    if "achievement_date" in update_data:

        update_data["achievement_date"] = (
            validate_achievement_date(
                update_data["achievement_date"]
            )
        )

    # -----------------------------------------------------
    # Clean optional fields
    # -----------------------------------------------------

    for field in [
        "category",
        "description",
        "certificate_url",
    ]:

        if field in update_data:

            value = update_data[field]

            if isinstance(value, str):

                value = value.strip()

                update_data[field] = (
                    value
                    if value
                    else None
                )

    # -----------------------------------------------------
    # Apply updates
    # -----------------------------------------------------

    for field, value in update_data.items():

        setattr(
            achievement,
            field,
            value,
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(achievement)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update achievement",
        )

    return build_achievement_response(
        achievement
    )


# =========================================================
# DELETE ACHIEVEMENT
# =========================================================
#
# DELETE /achievements/{achievement_id}
#
# =========================================================

@router.delete(
    "/{achievement_id}"
)
def delete_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    db.delete(achievement)

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete achievement",
        )

    return {
        "message": "Achievement deleted successfully"
    }


# =========================================================
# UPLOAD PROOF FILE
# =========================================================
#
# POST /achievements/{achievement_id}/file
#
# Requires authentication.
#
# =========================================================

@router.post(
    "/{achievement_id}/file",
)
async def upload_achievement_file(
    achievement_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find achievement
    # -----------------------------------------------------

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Validate file type
    # -----------------------------------------------------

    if file.content_type not in ALLOWED_FILE_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Allowed files: PDF, JPG, PNG, WEBP, "
                "DOC, DOCX, PPT, PPTX, XLS, XLSX and TXT"
            ),
        )

    # -----------------------------------------------------
    # Read file
    # -----------------------------------------------------

    file_data = await file.read()

    # -----------------------------------------------------
    # Validate size
    # -----------------------------------------------------

    if len(file_data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="File must be smaller than 10 MB",
        )

    if len(file_data) == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    achievement.certificate_file = file_data

    achievement.certificate_file_name = (
        file.filename
    )

    achievement.certificate_file_type = (
        file.content_type
    )

    achievement.certificate_file_size = (
        len(file_data)
    )

    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(achievement)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to upload achievement proof",
        )

    # -----------------------------------------------------
    # PUBLIC FILE URL
    # -----------------------------------------------------

    public_file_url = (
        f"/achievements/public/"
        f"{achievement.id}/file"
    )

    return {
        "message": (
            "Achievement proof uploaded successfully"
        ),

        "achievement_id":
            achievement.id,

        "file_name":
            achievement.certificate_file_name,

        "file_type":
            achievement.certificate_file_type,

        "file_size":
            achievement.certificate_file_size,

        "file_url":
            public_file_url,
    }


# =========================================================
# GET PROOF FILE - AUTHENTICATED
# =========================================================
#
# GET /achievements/{achievement_id}/file
#
# Requires authentication.
#
# Used for student/dashboard operations.
#
# =========================================================

@router.get(
    "/{achievement_id}/file"
)
def get_achievement_file(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find achievement
    # -----------------------------------------------------

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if not achievement.certificate_file:

        raise HTTPException(
            status_code=404,
            detail="Achievement proof file not found",
        )

    # -----------------------------------------------------
    # Return file
    # -----------------------------------------------------

    return Response(
        content=achievement.certificate_file,
        media_type=(
            achievement.certificate_file_type
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition": (
                f'inline; filename="{achievement.certificate_file_name}"'
            )
        },
    )


# =========================================================
# DELETE PROOF FILE
# =========================================================
#
# DELETE /achievements/{achievement_id}/file
#
# Requires authentication.
#
# =========================================================

@router.delete(
    "/{achievement_id}/file"
)
def delete_achievement_file(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find achievement
    # -----------------------------------------------------

    achievement = (
        db.query(Achievement)
        .filter(
            Achievement.id == achievement_id,
            Achievement.student_profile_id == profile.id,
        )
        .first()
    )

    if not achievement:

        raise HTTPException(
            status_code=404,
            detail="Achievement not found",
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if not achievement.certificate_file:

        raise HTTPException(
            status_code=404,
            detail="Achievement proof file not found",
        )

    # -----------------------------------------------------
    # Delete file
    # -----------------------------------------------------

    achievement.certificate_file = None

    achievement.certificate_file_name = None

    achievement.certificate_file_type = None

    achievement.certificate_file_size = None

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete achievement proof",
        )

    return {
        "message":
            "Achievement proof deleted successfully"
    }