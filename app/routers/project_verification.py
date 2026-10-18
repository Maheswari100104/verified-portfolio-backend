from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.project import Project
from app.models.project_verification import ProjectVerification

from app.models.student_profile import StudentProfile

from app.schemas.project_verification import (
    ProjectVerificationCreate,
    ProjectVerificationUpdate,
    ProjectVerificationResponse,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/project-verification",
    tags=["Project Verification"],
)


# =========================================================
# Helper
# Build Complete Project Verification Response
# =========================================================

def build_project_verification_response(
    verification: ProjectVerification,
    db: Session,
):
    # =====================================================
    # Find Student User
    # =====================================================

    student_user = (
        db.query(User)
        .filter(
            User.id == verification.student_id,
            User.role == "student",
        )
        .first()
    )

    if not student_user:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    # =====================================================
    # Find Student Profile
    # =====================================================

    student_profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == student_user.id
        )
        .first()
    )

    # =====================================================
    # Find Project
    # =====================================================

    project = (
        db.query(Project)
        .filter(
            Project.id == verification.project_id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    # =====================================================
    # Convert Technologies
    # =====================================================

    technologies = []

    if project.technologies:
        technologies = [
            technology.strip()
            for technology in project.technologies.split(",")
            if technology.strip()
        ]

    # =====================================================
    # Student Information
    # =====================================================

    student_data = {
        "id": student_user.id,

        "name": (
            student_profile.full_name
            if student_profile
            else "Student"
        ),

        "email": student_user.email,

        "headline": (
            student_profile.headline
            if student_profile
            else ""
        ),
    }

    # =====================================================
    # Project Information
    # =====================================================

    project_data = {
        "id": project.id,

        "title": project.title,

        "description": project.description,

        "technologies": technologies,

        "github": project.github,

        "live_demo": project.live_demo,

        "image": project.image,

        "start_date": (
            project.start_date.isoformat()
            if project.start_date
            else None
        ),

        "end_date": (
            project.end_date.isoformat()
            if project.end_date
            else None
        ),

        "is_current": project.is_current,
    }

    # =====================================================
    # Final Response
    # =====================================================

    return {
        "id": verification.id,

        "project_id": verification.project_id,

        "student_id": verification.student_id,

        "mentor_id": verification.mentor_id,

        "status": verification.status,

        # =================================================
        # Rating
        # =================================================

        "rating": verification.rating,

        # =================================================
        # Feedback
        # =================================================

        "feedback": verification.feedback,

        # =================================================
        # Comment
        # =================================================

        "comment": verification.comment,

        "is_verified": verification.is_verified,

        "verified_at": verification.verified_at,

        "created_at": verification.created_at,

        "updated_at": verification.updated_at,

        "student": student_data,

        "project": project_data,
    }


# =========================================================
# Student → Submit Project for Verification
# =========================================================

@router.post(
    "/request",
    response_model=ProjectVerificationResponse,
)
def submit_project_for_verification(
    request: ProjectVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Student Only
    # =====================================================

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can submit projects "
                "for verification."
            ),
        )

    # =====================================================
    # Find Student Project
    # =====================================================

    project = (
        db.query(Project)
        .join(
            StudentProfile,
            Project.student_profile_id == StudentProfile.id,
        )
        .filter(
            Project.id == request.project_id,
            StudentProfile.user_id == current_user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    # =====================================================
    # Find Selected Mentor
    # =====================================================

    mentor = (
        db.query(User)
        .filter(
            User.id == request.mentor_id,
            User.role == "mentor",
            User.is_active == True,
        )
        .first()
    )

    if not mentor:
        raise HTTPException(
            status_code=404,
            detail="Selected mentor not found.",
        )

   
    # =====================================================
    # Check Existing Verification
    # =====================================================

    existing_verification = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.project_id
            == project.id
        )
        .first()
    )

    # =====================================================
    # Existing Verification
    # =====================================================

    if existing_verification:

        # -------------------------------------------------
        # Pending
        # -------------------------------------------------

        if existing_verification.status == "pending":
            raise HTTPException(
                status_code=409,
                detail=(
                    "This project is already waiting "
                    "for mentor verification."
                ),
            )

        # -------------------------------------------------
        # Verified
        # -------------------------------------------------

        if existing_verification.status == "verified":
            raise HTTPException(
                status_code=409,
                detail=(
                    "This project has already "
                    "been verified."
                ),
            )

        # -------------------------------------------------
        # Rejected → Resubmit
        # -------------------------------------------------

        if existing_verification.status == "rejected":

            existing_verification.status = "pending"

            existing_verification.mentor_id = (
                request.mentor_id
            )

            existing_verification.feedback = None

            # Reset rating when resubmitting
            existing_verification.rating = None

            existing_verification.comment = (
                request.comment
            )

            existing_verification.is_verified = False

            existing_verification.verified_at = None

            existing_verification.updated_at = (
                datetime.now(timezone.utc)
            )

            try:
                db.commit()
                db.refresh(existing_verification)

            except Exception:
                db.rollback()

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Unable to resubmit project "
                        "for verification."
                    ),
                )

            return build_project_verification_response(
                existing_verification,
                db,
            )

    # =====================================================
    # Create New Verification Request
    # =====================================================

    verification = ProjectVerification(
        project_id=project.id,

        student_id=current_user.id,

        mentor_id=request.mentor_id,

        status="pending",

        feedback=None,

        # No rating before mentor reviews
        rating=None,

        comment=request.comment,

        is_verified=False,

        verified_at=None,
    )

    db.add(verification)

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(verification)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to submit project "
                "for verification."
            ),
        )

    # =====================================================
    # Return Response
    # =====================================================

    return build_project_verification_response(
        verification,
        db,
    )


# =========================================================
# Student → View My Verification Requests
# =========================================================

@router.get(
    "/my-requests",
    response_model=list[ProjectVerificationResponse],
)
def get_my_project_verification_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Student Only
    # =====================================================

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can view their "
                "verification requests."
            ),
        )

    # =====================================================
    # Get Student Requests
    # =====================================================

    requests = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.student_id
            == current_user.id
        )
        .order_by(
            ProjectVerification.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Build Response
    # =====================================================

    response = []

    for verification in requests:
        response.append(
            build_project_verification_response(
                verification,
                db,
            )
        )

    return response


# =========================================================
# Mentor → View Pending Project Verifications
# =========================================================

@router.get(
    "/requests",
    response_model=list[ProjectVerificationResponse],
)
def get_project_verification_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Mentor Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only mentors can view "
                "verification requests."
            ),
        )

    # =====================================================
    # Get Pending Requests
    # =====================================================

    requests = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.mentor_id
            == current_user.id,

            ProjectVerification.status
            == "pending",
        )
        .order_by(
            ProjectVerification.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Build Response
    # =====================================================

    response = []

    for verification in requests:
        response.append(
            build_project_verification_response(
                verification,
                db,
            )
        )

    return response


# =========================================================
# Mentor → View Single Verification Request
# =========================================================

@router.get(
    "/requests/{verification_id}",
    response_model=ProjectVerificationResponse,
)
def get_project_verification(
    verification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Mentor Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only mentors can view "
                "verification requests."
            ),
        )

    # =====================================================
    # Find Verification
    # =====================================================

    verification = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.id
            == verification_id,

            ProjectVerification.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification request not found.",
        )

    # =====================================================
    # Return Response
    # =====================================================

    return build_project_verification_response(
        verification,
        db,
    )


# =========================================================
# Mentor → Verify / Reject Project
# =========================================================

@router.put(
    "/requests/{verification_id}",
    response_model=ProjectVerificationResponse,
)
def update_project_verification(
    verification_id: int,
    request: ProjectVerificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Mentor Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only mentors can verify "
                "or reject projects."
            ),
        )

    # =====================================================
    # Find Verification
    # =====================================================

    verification = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.id
            == verification_id,

            ProjectVerification.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification request not found.",
        )

    # =====================================================
    # Only Pending Can Be Processed
    # =====================================================

    if verification.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This verification request has "
                "already been processed."
            ),
        )

    # =====================================================
    # Validate Rating
    # =====================================================

    if request.rating is not None:

        if request.rating < 1 or request.rating > 5:
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 1 and 5.",
            )

    # =====================================================
    # Require Rating When Verifying
    # =====================================================

    if (
        request.status == "verified"
        and request.rating is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Please provide a rating "
                "before verifying the project."
            ),
        )

    # =====================================================
    # Require Feedback
    # =====================================================

    if not request.feedback or not request.feedback.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "Please provide feedback "
                "before processing the project."
            ),
        )

    # =====================================================
    # Update Status
    # =====================================================

    verification.status = request.status

    # =====================================================
    # Save Rating
    # =====================================================

    verification.rating = request.rating

    # =====================================================
    # Save Feedback
    # =====================================================

    verification.feedback = request.feedback.strip()

    # =====================================================
    # Save Comment
    # =====================================================

    verification.comment = request.comment

    verification.updated_at = (
        datetime.now(timezone.utc)
    )

    # =====================================================
    # VERIFIED
    # =====================================================

    if request.status == "verified":

        verification.is_verified = True

        verification.verified_at = (
            datetime.now(timezone.utc)
        )

    # =====================================================
    # REJECTED
    # =====================================================

    else:

        verification.is_verified = False

        verification.verified_at = None

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(verification)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to update "
                "project verification."
            ),
        )

    # =====================================================
    # Return Updated Verification
    # =====================================================

    return build_project_verification_response(
        verification,
        db,
    )