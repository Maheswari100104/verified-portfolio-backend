from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.user import User
from app.models.mentor_profile import MentorProfile

from app.schemas.mentor import (
    MentorProfileCreate,
    MentorProfileUpdate,
    MentorProfileResponse,
    MentorListResponse,
)

from app.core.dependencies import get_current_user

from app.services.mentor_ocr import (
    extract_text_from_image,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/mentor",
    tags=["Mentor"],
)


# =========================================================
# Helper - Verify Mentor Role
# =========================================================

def verify_mentor(
    current_user: User,
):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail="Only mentors can access this resource",
        )


# =========================================================
# Helper - Update Profile Verification Status
# =========================================================

def update_profile_verification_status(
    mentor_profile: MentorProfile,
):
    full_name = (
        mentor_profile.full_name or ""
    ).strip()

    institution = (
        mentor_profile.institution or ""
    ).strip()

    designation = (
        mentor_profile.designation or ""
    ).strip()

    if (
        full_name
        and institution
        and designation
    ):
        mentor_profile.verification_status = "verified"

    else:
        mentor_profile.verification_status = "pending"

        mentor_profile.verified_at = None
        mentor_profile.verified_by = None


# =========================================================
# STUDENT → GET AVAILABLE MENTORS
# =========================================================
#
# URL:
#
# GET /mentor/mentors
#
# Students use this endpoint to browse mentors.
#
# Only mentors with a completed/verified profile are
# returned.
#
# =========================================================

@router.get(
    "/mentors",
    response_model=list[MentorListResponse],
)
def get_available_mentors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Only students can browse mentors
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can browse mentors.",
        )

    # -----------------------------------------------------
    # Get verified mentor profiles
    # -----------------------------------------------------

    mentor_profiles = (
        db.query(MentorProfile)
        .join(
            User,
            MentorProfile.user_id == User.id,
        )
        .filter(
            User.role == "mentor",
            User.is_active == True,
            MentorProfile.verification_status == "verified",
        )
        .order_by(
            MentorProfile.full_name.asc()
        )
        .all()
    )

    mentors = []

    for mentor_profile in mentor_profiles:

        mentor_user = (
            db.query(User)
            .filter(
                User.id == mentor_profile.user_id,
                User.role == "mentor",
                User.is_active == True,
            )
            .first()
        )

        if not mentor_user:
            continue

        mentors.append(
            {
                "id": mentor_user.id,

                "name": (
                    mentor_profile.full_name
                ),

                "email": (
                    mentor_user.email
                ),

                "specialization": (
                    mentor_profile.specialization
                ),

                "designation": (
                    mentor_profile.designation
                ),

                "institution": (
                    mentor_profile.institution
                ),

                "department": (
                    mentor_profile.department
                ),

                "location": (
                    mentor_profile.location
                ),

                "mentor_type": (
                    mentor_profile.mentor_type
                ),

                "about": (
                    mentor_profile.about
                ),

                "verification_status": (
                    mentor_profile.verification_status
                ),

                "ai_verified": (
                    mentor_profile.ai_verified
                ),
            }
        )

    return mentors


# =========================================================
# GET CURRENT MENTOR PROFILE
# =========================================================

@router.get(
    "/profile",
    response_model=MentorProfileResponse,
)
def get_mentor_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_mentor(current_user)

    mentor_profile = (
        db.query(MentorProfile)
        .filter(
            MentorProfile.user_id == current_user.id
        )
        .first()
    )

    if not mentor_profile:
        raise HTTPException(
            status_code=404,
            detail="Mentor profile not found",
        )

    return mentor_profile


# =========================================================
# CREATE MENTOR PROFILE
# =========================================================

@router.post(
    "/profile",
    response_model=MentorProfileResponse,
)
def create_mentor_profile(
    request: MentorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_mentor(current_user)

    existing_profile = (
        db.query(MentorProfile)
        .filter(
            MentorProfile.user_id == current_user.id
        )
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=409,
            detail="Mentor profile already exists",
        )

    mentor_type = (
        request.mentor_type
        .lower()
        .strip()
    )

    if mentor_type not in {
        "teacher",
        "trainer",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mentor type must be either "
                "teacher or trainer"
            ),
        )

    mentor_profile = MentorProfile(
        user_id=current_user.id,

        full_name=request.full_name.strip(),

        phone=(
            request.phone.strip()
            if request.phone
            else None
        ),

        mentor_type=mentor_type,

        institution=(
            request.institution.strip()
            if request.institution
            else None
        ),

        institution_email=(
            request.institution_email
            .strip()
            .lower()
            if request.institution_email
            else None
        ),

        department=(
            request.department.strip()
            if request.department
            else None
        ),

        designation=(
            request.designation.strip()
            if request.designation
            else None
        ),

        specialization=(
            request.specialization.strip()
            if request.specialization
            else None
        ),

        location=(
            request.location.strip()
            if request.location
            else None
        ),

        about=(
            request.about.strip()
            if request.about
            else None
        ),

        verification_status="pending",

        ai_verified=False,
    )

    update_profile_verification_status(
        mentor_profile
    )

    db.add(mentor_profile)

    try:
        db.commit()
        db.refresh(mentor_profile)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create mentor profile",
        )

    return mentor_profile


# =========================================================
# UPDATE MENTOR PROFILE
# =========================================================

@router.put(
    "/profile",
    response_model=MentorProfileResponse,
)
def update_mentor_profile(
    request: MentorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_mentor(current_user)

    mentor_profile = (
        db.query(MentorProfile)
        .filter(
            MentorProfile.user_id == current_user.id
        )
        .first()
    )

    if not mentor_profile:
        raise HTTPException(
            status_code=404,
            detail="Mentor profile not found",
        )

    # -----------------------------------------------------
    # Mentor Type
    # -----------------------------------------------------

    if request.mentor_type is not None:

        mentor_type = (
            request.mentor_type
            .lower()
            .strip()
        )

        if mentor_type not in {
            "teacher",
            "trainer",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Mentor type must be either "
                    "teacher or trainer"
                ),
            )

        mentor_profile.mentor_type = mentor_type

    # -----------------------------------------------------
    # Basic Details
    # -----------------------------------------------------

    if request.full_name is not None:
        mentor_profile.full_name = (
            request.full_name.strip()
        )

    if request.phone is not None:
        mentor_profile.phone = (
            request.phone.strip()
        )

    # -----------------------------------------------------
    # Professional Details
    # -----------------------------------------------------

    if request.institution is not None:
        mentor_profile.institution = (
            request.institution.strip()
        )

    if request.institution_email is not None:
        mentor_profile.institution_email = (
            request.institution_email
            .strip()
            .lower()
        )

    if request.department is not None:
        mentor_profile.department = (
            request.department.strip()
        )

    if request.designation is not None:
        mentor_profile.designation = (
            request.designation.strip()
        )

    if request.specialization is not None:
        mentor_profile.specialization = (
            request.specialization.strip()
        )

    if request.location is not None:
        mentor_profile.location = (
            request.location.strip()
        )

    # -----------------------------------------------------
    # About
    # -----------------------------------------------------

    if request.about is not None:
        mentor_profile.about = (
            request.about.strip()
        )

    # -----------------------------------------------------
    # Recalculate Verification
    # -----------------------------------------------------

    update_profile_verification_status(
        mentor_profile
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()
        db.refresh(mentor_profile)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update mentor profile",
        )

    return mentor_profile


# =========================================================
# UPLOAD MENTOR VERIFICATION DOCUMENT
# =========================================================

@router.post(
    "/profile/verification-document",
)
async def upload_verification_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_mentor(current_user)

    mentor_profile = (
        db.query(MentorProfile)
        .filter(
            MentorProfile.user_id == current_user.id
        )
        .first()
    )

    if not mentor_profile:
        raise HTTPException(
            status_code=404,
            detail="Mentor profile not found",
        )

    # -----------------------------------------------------
    # Validate File Type
    # -----------------------------------------------------

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/jpg",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, JPEG and PNG files "
                "are currently supported"
            ),
        )

    # -----------------------------------------------------
    # Read File
    # -----------------------------------------------------

    file_data = await file.read()

    # -----------------------------------------------------
    # Validate File Size
    # -----------------------------------------------------

    max_file_size = 5 * 1024 * 1024

    if len(file_data) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail=(
                "Verification document "
                "must be smaller than 5 MB"
            ),
        )

    if len(file_data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    # -----------------------------------------------------
    # Store Document
    # -----------------------------------------------------

    mentor_profile.verification_document = (
        file_data
    )

    mentor_profile.verification_document_name = (
        file.filename
    )

    mentor_profile.verification_document_type = (
        file.content_type
    )

    mentor_profile.verification_document_size = (
        len(file_data)
    )

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    extracted_text = ""

    ocr_message = (
        "Verification document uploaded successfully."
    )

    try:

        extracted_text = extract_text_from_image(
            file_data
        )

        if extracted_text:

            mentor_profile.ocr_extracted_text = (
                extracted_text
            )

            ocr_message = (
                "Verification document uploaded "
                "and OCR completed successfully."
            )

        else:

            mentor_profile.ocr_extracted_text = ""

            ocr_message = (
                "Verification document uploaded, "
                "but no readable text was found."
            )

    except Exception as error:

        print(
            "OCR extraction warning:",
            error,
        )

        mentor_profile.ocr_extracted_text = ""

        ocr_message = (
            "Verification document uploaded successfully. "
            "OCR extraction was unavailable."
        )

    # -----------------------------------------------------
    # Recalculate Verification
    # -----------------------------------------------------

    update_profile_verification_status(
        mentor_profile
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:
        db.commit()
        db.refresh(mentor_profile)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save verification document"
            ),
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": ocr_message,

        "file_name": (
            mentor_profile.verification_document_name
        ),

        "file_type": (
            mentor_profile.verification_document_type
        ),

        "file_size": (
            mentor_profile.verification_document_size
        ),

        "verification_status": (
            mentor_profile.verification_status
        ),

        "ocr_extracted_text": (
            mentor_profile.ocr_extracted_text
            or ""
        ),
    }