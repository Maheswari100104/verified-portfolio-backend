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

from app.models import StudentProfile
from app.models.user import User

from app.schemas.student_profile import (
    StudentProfileCreate,
    StudentProfileResponse,
)

from app.core.dependencies import get_current_user


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/student/profile",
    tags=["Student Profile"],
)


# =========================================================
# Constants
# =========================================================

BACKEND_URL = "http://127.0.0.1:8000"

MAX_PROFILE_PHOTO_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


# =========================================================
# Helper: Profile Photo URL
# =========================================================

def get_profile_photo_url() -> str:
    return (
        f"{BACKEND_URL}"
        "/student/profile/me/photo"
    )


# =========================================================
# GET MY STUDENT PROFILE
# =========================================================
#
# GET /student/profile/me
#
# Returns the logged-in student's profile.
#
# =========================================================

@router.get(
    "/me",
    response_model=StudentProfileResponse,
)
def get_my_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access student profiles",
        )

    # -----------------------------------------------------
    # Find profile
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

    # -----------------------------------------------------
    # Build response
    # -----------------------------------------------------

    response = StudentProfileResponse.model_validate(
        profile
    )

    # -----------------------------------------------------
    # Add photo URL
    # -----------------------------------------------------

    if profile.profile_photo:
        response.profile_photo_url = (
            get_profile_photo_url()
        )
    else:
        response.profile_photo_url = None

    return response


# =========================================================
# CREATE MY STUDENT PROFILE
# =========================================================
#
# POST /student/profile/me
#
# =========================================================

@router.post(
    "/me",
    response_model=StudentProfileResponse,
)
def create_my_student_profile(
    profile: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can create student profiles",
        )

    # -----------------------------------------------------
    # Check existing profile
    # -----------------------------------------------------

    existing_profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == current_user.id
        )
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Student profile already exists",
        )

    # -----------------------------------------------------
    # Optional email update during profile creation
    # -----------------------------------------------------

    if profile.email:
        new_email = profile.email.strip()

        if new_email != current_user.email:

            existing_user = (
                db.query(User)
                .filter(
                    User.email == new_email,
                    User.id != current_user.id,
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This email address is already "
                        "registered with another account."
                    ),
                )

            current_user.email = new_email

    # -----------------------------------------------------
    # Create profile
    # -----------------------------------------------------

    new_profile = StudentProfile(
        user_id=current_user.id,
        full_name=profile.full_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        linkedin=profile.linkedin,
        github=profile.github,
        website=profile.website,
        about=profile.about,
    )

    db.add(new_profile)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()

        db.refresh(current_user)
        db.refresh(new_profile)

    except Exception as error:
        db.rollback()

        print(
            "Failed to create student profile:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create student profile",
        )

    # -----------------------------------------------------
    # Build response
    # -----------------------------------------------------

    response = StudentProfileResponse.model_validate(
        new_profile
    )

    response.profile_photo_url = None

    return response


# =========================================================
# UPDATE MY STUDENT PROFILE
# =========================================================
#
# PUT /student/profile/me
#
# Updates:
#   - Email
#   - Full name
#   - Phone
#   - Location
#   - Headline
#   - LinkedIn
#   - GitHub
#   - Website
#   - About
#
# Profile photo is handled separately.
#
# =========================================================

@router.put(
    "/me",
    response_model=StudentProfileResponse,
)
def update_my_student_profile(
    profile: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can update student profiles",
        )

    # -----------------------------------------------------
    # Find profile
    # -----------------------------------------------------

    existing_profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == current_user.id
        )
        .first()
    )

    if not existing_profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    # =====================================================
    # UPDATE EMAIL
    # =====================================================
    #
    # Email is stored in the User table, not
    # StudentProfile table.
    #
    # =====================================================

    if profile.email:

        new_email = profile.email.strip()

        # -------------------------------------------------
        # Check whether email was actually changed
        # -------------------------------------------------

        if new_email != current_user.email:

            # ---------------------------------------------
            # Check whether another account already
            # uses this email
            # ---------------------------------------------

            existing_user = (
                db.query(User)
                .filter(
                    User.email == new_email,
                    User.id != current_user.id,
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This email address is already "
                        "registered with another account."
                    ),
                )

            # ---------------------------------------------
            # Update User email
            # ---------------------------------------------

            current_user.email = new_email

    # =====================================================
    # UPDATE STUDENT PROFILE FIELDS
    # =====================================================

    existing_profile.full_name = profile.full_name
    existing_profile.phone = profile.phone
    existing_profile.location = profile.location
    existing_profile.headline = profile.headline
    existing_profile.linkedin = profile.linkedin
    existing_profile.github = profile.github
    existing_profile.website = profile.website
    existing_profile.about = profile.about

    # =====================================================
    # SAVE BOTH USER + STUDENT PROFILE
    # =====================================================

    try:

        db.commit()

        db.refresh(current_user)
        db.refresh(existing_profile)

    except Exception as error:

        db.rollback()

        print(
            "Failed to update student profile:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update student profile",
        )

    # =====================================================
    # BUILD RESPONSE
    # =====================================================

    response = StudentProfileResponse.model_validate(
        existing_profile
    )

    # -----------------------------------------------------
    # Include photo URL
    # -----------------------------------------------------

    if existing_profile.profile_photo:
        response.profile_photo_url = (
            get_profile_photo_url()
        )
    else:
        response.profile_photo_url = None

    return response


# =========================================================
# UPLOAD MY PROFILE PHOTO
# =========================================================
#
# POST /student/profile/me/photo
#
# Stores the actual image bytes in the database.
#
# =========================================================

@router.post("/me/photo")
async def upload_my_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can upload profile photos",
        )

    # -----------------------------------------------------
    # Find profile
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

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected",
        )

    # -----------------------------------------------------
    # Validate file type
    # -----------------------------------------------------

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG, WEBP, and GIF "
                "images are allowed"
            ),
        )

    # -----------------------------------------------------
    # Read file
    # -----------------------------------------------------

    file_data = await file.read()

    # -----------------------------------------------------
    # Validate empty file
    # -----------------------------------------------------

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="The selected image is empty",
        )

    # -----------------------------------------------------
    # Validate file size
    # -----------------------------------------------------

    if len(file_data) > MAX_PROFILE_PHOTO_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image size should be less than 5 MB",
        )

    # -----------------------------------------------------
    # Store image
    # -----------------------------------------------------

    profile.profile_photo = file_data
    profile.profile_photo_name = file.filename
    profile.profile_photo_type = file.content_type
    profile.profile_photo_size = len(file_data)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()
        db.refresh(profile)

    except Exception as error:

        db.rollback()

        print(
            "Failed to upload profile photo:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to upload profile photo",
        )

    # -----------------------------------------------------
    # Return information
    # -----------------------------------------------------

    return {
        "message": "Profile photo uploaded successfully",
        "file_name": profile.profile_photo_name,
        "file_type": profile.profile_photo_type,
        "file_size": profile.profile_photo_size,
        "photo_url": get_profile_photo_url(),
    }


# =========================================================
# GET MY PROFILE PHOTO
# =========================================================
#
# GET /student/profile/me/photo
#
# =========================================================

@router.get("/me/photo")
def get_my_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access student photos",
        )

    # -----------------------------------------------------
    # Find profile
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

    # -----------------------------------------------------
    # Check photo
    # -----------------------------------------------------

    if not profile.profile_photo:
        raise HTTPException(
            status_code=404,
            detail="Profile photo not found",
        )

    # -----------------------------------------------------
    # Return image
    # -----------------------------------------------------

    return Response(
        content=profile.profile_photo,
        media_type=(
            profile.profile_photo_type
            or "application/octet-stream"
        ),
        headers={
            "Cache-Control": "no-cache",
        },
    )


# =========================================================
# DELETE MY PROFILE PHOTO
# =========================================================
#
# DELETE /student/profile/me/photo
#
# =========================================================

@router.delete("/me/photo")
def delete_my_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can remove profile photos",
        )

    # -----------------------------------------------------
    # Find profile
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

    # -----------------------------------------------------
    # Check photo
    # -----------------------------------------------------

    if not profile.profile_photo:
        raise HTTPException(
            status_code=404,
            detail="Profile photo not found",
        )

    # -----------------------------------------------------
    # Remove photo
    # -----------------------------------------------------

    profile.profile_photo = None
    profile.profile_photo_name = None
    profile.profile_photo_type = None
    profile.profile_photo_size = None

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()
        db.refresh(profile)

    except Exception as error:

        db.rollback()

        print(
            "Failed to remove profile photo:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to remove profile photo",
        )

    return {
        "message": "Profile photo removed successfully"
    }