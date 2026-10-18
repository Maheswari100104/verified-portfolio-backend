from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.mentor_student import MentorStudent
from app.models.endorsement import Endorsement

from app.schemas.endorsement import (
    EndorsementCreate,
    EndorsementUpdate,
    EndorsementResponse,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/endorsements",
    tags=["Endorsements"],
)


# =========================================================
# Allowed Endorsement Types
# =========================================================

ALLOWED_ITEM_TYPES = {
    "skill",
    "project",
    "experience",
    "achievement",
}


# =========================================================
# Helper
# Build Complete Endorsement Response
# =========================================================

def build_endorsement_response(
    endorsement: Endorsement,
    db: Session,
):
    # =====================================================
    # Find Student User
    # =====================================================

    student = (
        db.query(User)
        .filter(
            User.id == endorsement.student_id,
            User.role == "student",
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    # =====================================================
    # Find Student Profile
    # =====================================================

    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == student.id
        )
        .first()
    )

    # =====================================================
    # Student Information
    # =====================================================

    student_data = {
        "id": student.id,

        "name": (
            profile.full_name
            if profile and profile.full_name
            else "Student"
        ),

        "email": student.email,

        "headline": (
            profile.headline
            if profile and profile.headline
            else ""
        ),
    }

    # =====================================================
    # Final Response
    # =====================================================

    return {
        "id": endorsement.id,

        "student_id": endorsement.student_id,

        "mentor_id": endorsement.mentor_id,

        "item_type": endorsement.item_type,

        "item_id": endorsement.item_id,

        "item_name": endorsement.item_name,

        "message": endorsement.message,

        "mentor_comment": endorsement.mentor_comment,

        "status": endorsement.status,

        "is_endorsed": endorsement.is_endorsed,

        "created_at": endorsement.created_at,

        "updated_at": endorsement.updated_at,

        "student": student_data,
    }


# =========================================================
# Student → Request Endorsement
# =========================================================

@router.post(
    "/request",
    response_model=EndorsementResponse,
)
def create_endorsement_request(
    request: EndorsementCreate,
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
                "Only students can request "
                "endorsements."
            ),
        )

    # =====================================================
    # Validate Item Type
    # =====================================================

    item_type = request.item_type.strip().lower()

    if item_type not in ALLOWED_ITEM_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Item type must be one of "
                "'skill', 'project', 'experience', "
                "or 'achievement'."
            ),
        )

    # =====================================================
    # Validate Item Name
    # =====================================================

    if not request.item_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Item name cannot be empty.",
        )

    # =====================================================
    # Find Mentor
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
    # Check Student → Mentor Connection
    # =====================================================

    connection = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.student_id == current_user.id,

            MentorStudent.mentor_id
            == request.mentor_id,

            MentorStudent.status == "accepted",

            MentorStudent.is_active == True,
        )
        .first()
    )

    if not connection:
        raise HTTPException(
            status_code=403,
            detail=(
                "You can only request an endorsement "
                "from a mentor who has accepted your "
                "mentor request."
            ),
        )

    # =====================================================
    # Check Existing Pending Request
    # =====================================================

    existing = (
        db.query(Endorsement)
        .filter(
            Endorsement.student_id
            == current_user.id,

            Endorsement.mentor_id
            == request.mentor_id,

            Endorsement.item_type
            == item_type,

            Endorsement.item_id
            == request.item_id,

            Endorsement.status
            == "pending",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "An endorsement request for this "
                "item is already pending."
            ),
        )

    # =====================================================
    # Create Endorsement
    # =====================================================

    endorsement = Endorsement(
        student_id=current_user.id,

        mentor_id=request.mentor_id,

        item_type=item_type,

        item_id=request.item_id,

        item_name=request.item_name.strip(),

        message=(
            request.message.strip()
            if request.message
            else None
        ),

        mentor_comment=None,

        status="pending",

        is_endorsed=False,
    )

    db.add(endorsement)

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(endorsement)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create endorsement "
                "request."
            ),
        )

    # =====================================================
    # Return Response
    # =====================================================

    return build_endorsement_response(
        endorsement,
        db,
    )


# =========================================================
# Student → View My Endorsement Requests
# =========================================================

@router.get(
    "/my-requests",
    response_model=list[EndorsementResponse],
)
def get_my_endorsement_requests(
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
                "Only students can view "
                "their endorsement requests."
            ),
        )

    # =====================================================
    # Get Student Requests
    # =====================================================

    endorsements = (
        db.query(Endorsement)
        .filter(
            Endorsement.student_id
            == current_user.id
        )
        .order_by(
            Endorsement.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Return Requests
    # =====================================================

    return [
        build_endorsement_response(
            endorsement,
            db,
        )
        for endorsement in endorsements
    ]


# =========================================================
# Mentor → View Endorsement Requests
# =========================================================

@router.get(
    "/requests",
    response_model=list[EndorsementResponse],
)
def get_endorsement_requests(
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
                "endorsement requests."
            ),
        )

    # =====================================================
    # Get Mentor Requests
    # =====================================================

    endorsements = (
        db.query(Endorsement)
        .filter(
            Endorsement.mentor_id
            == current_user.id
        )
        .order_by(
            Endorsement.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Return Requests
    # =====================================================

    return [
        build_endorsement_response(
            endorsement,
            db,
        )
        for endorsement in endorsements
    ]


# =========================================================
# Mentor → View Single Endorsement
# =========================================================

@router.get(
    "/requests/{endorsement_id}",
    response_model=EndorsementResponse,
)
def get_endorsement_request(
    endorsement_id: int,
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
                "endorsement requests."
            ),
        )

    # =====================================================
    # Find Request
    # =====================================================

    endorsement = (
        db.query(Endorsement)
        .filter(
            Endorsement.id
            == endorsement_id,

            Endorsement.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not endorsement:
        raise HTTPException(
            status_code=404,
            detail=(
                "Endorsement request "
                "not found."
            ),
        )

    # =====================================================
    # Return Request
    # =====================================================

    return build_endorsement_response(
        endorsement,
        db,
    )


# =========================================================
# Mentor → Endorse / Reject
# =========================================================

@router.put(
    "/requests/{endorsement_id}",
    response_model=EndorsementResponse,
)
def update_endorsement(
    endorsement_id: int,
    request: EndorsementUpdate,
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
                "Only mentors can process "
                "endorsement requests."
            ),
        )

    # =====================================================
    # Validate Status
    # =====================================================

    status = request.status.strip().lower()

    if status not in [
        "endorsed",
        "rejected",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be either "
                "'endorsed' or 'rejected'."
            ),
        )

    # =====================================================
    # Find Endorsement
    # =====================================================

    endorsement = (
        db.query(Endorsement)
        .filter(
            Endorsement.id
            == endorsement_id,

            Endorsement.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not endorsement:
        raise HTTPException(
            status_code=404,
            detail=(
                "Endorsement request "
                "not found."
            ),
        )

    # =====================================================
    # Only Pending Can Be Processed
    # =====================================================

    if endorsement.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This endorsement request has "
                "already been processed."
            ),
        )

    # =====================================================
    # Update Status
    # =====================================================

    endorsement.status = status

    # =====================================================
    # Update Endorsed Flag
    # =====================================================

    if status == "endorsed":
        endorsement.is_endorsed = True
    else:
        endorsement.is_endorsed = False

    # =====================================================
    # Mentor Comment
    # =====================================================

    if request.mentor_comment:
        endorsement.mentor_comment = (
            request.mentor_comment.strip()
        )
    else:
        endorsement.mentor_comment = None

    # =====================================================
    # Updated Time
    # =====================================================

    endorsement.updated_at = (
        datetime.now(timezone.utc)
    )

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(endorsement)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to update "
                "endorsement request."
            ),
        )

    # =====================================================
    # Return Updated Request
    # =====================================================

    return build_endorsement_response(
        endorsement,
        db,
    )