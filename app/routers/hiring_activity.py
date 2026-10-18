from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User

from app.models.project_verification import ProjectVerification
from app.models.project import Project

from app.models.experience_verification import (
    ExperienceVerification,
)
from app.models.experience import Experience

from app.models.endorsement import Endorsement

from app.models.opportunity import Opportunity

from app.models.shortlisted_candidate import (
    ShortlistedCandidate,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/hiring",
    tags=["Hiring Activity"],
)


# =========================================================
# Helper
# Safely convert date/datetime to ISO string
# =========================================================

def safe_datetime(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


# =========================================================
# GET HIRING ACTIVITY
# IT PROFESSIONAL ONLY
# =========================================================

@router.get("/activity")
def get_hiring_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Mentor / IT Professional only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can view "
                "hiring activity."
            ),
        )

    activities = []

    # =====================================================
    # 1. PROJECT VERIFICATION ACTIVITY
    # =====================================================

    project_verifications = (
        db.query(ProjectVerification)
        .filter(
            ProjectVerification.mentor_id
            == current_user.id,

            # Only completed actions should appear.
            ProjectVerification.status.in_(
                ["verified", "rejected"]
            ),
        )
        .order_by(
            ProjectVerification.updated_at.desc()
        )
        .all()
    )

    for verification in project_verifications:

        project = (
            db.query(Project)
            .filter(
                Project.id
                == verification.project_id
            )
            .first()
        )

        project_title = (
            project.title
            if project and project.title
            else "a project"
        )

        student = (
            db.query(User)
            .filter(
                User.id
                == verification.student_id,
                User.role == "student",
            )
            .first()
        )

        student_name = (
            "Student"
        )

        if student:
            # Student profile is optional here.
            from app.models.student_profile import (
                StudentProfile,
            )

            profile = (
                db.query(StudentProfile)
                .filter(
                    StudentProfile.user_id
                    == student.id
                )
                .first()
            )

            if (
                profile
                and profile.full_name
            ):
                student_name = (
                    profile.full_name
                )

        # ---------------------------------------------
        # Verified
        # ---------------------------------------------

        if verification.status == "verified":

            activities.append(
                {
                    "id": verification.id,
                    "type": "verification",
                    "title": "Verified a project",
                    "message": (
                        f'Verified "{project_title}" '
                        f"submitted by "
                        f"{student_name}."
                    ),
                    "description": (
                        verification.feedback
                        or verification.comment
                        or None
                    ),
                    "created_at": safe_datetime(
                        verification.updated_at
                        or verification.created_at
                    ),
                }
            )

        # ---------------------------------------------
        # Rejected
        # ---------------------------------------------

        elif (
            verification.status
            == "rejected"
        ):

            activities.append(
                {
                    "id": verification.id,
                    "type": "rejection",
                    "title": "Rejected a project",
                    "message": (
                        f'Rejected "{project_title}" '
                        f"submitted by "
                        f"{student_name}."
                    ),
                    "description": (
                        verification.feedback
                        or verification.comment
                        or None
                    ),
                    "created_at": safe_datetime(
                        verification.updated_at
                        or verification.created_at
                    ),
                }
            )

    # =====================================================
    # 2. EXPERIENCE VERIFICATION ACTIVITY
    # =====================================================

    experience_verifications = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.mentor_id
            == current_user.id,

            ExperienceVerification.status.in_(
                ["verified", "rejected"]
            ),
        )
        .order_by(
            ExperienceVerification.updated_at.desc()
        )
        .all()
    )

    for verification in experience_verifications:

        experience = (
            db.query(Experience)
            .filter(
                Experience.id
                == verification.experience_id
            )
            .first()
        )

        if experience:
            experience_name = (
                experience.position
                or experience.company
                or "experience"
            )
        else:
            experience_name = "experience"

        student = (
            db.query(User)
            .filter(
                User.id
                == verification.student_id,
                User.role == "student",
            )
            .first()
        )

        student_name = "Student"

        if student:
            from app.models.student_profile import (
                StudentProfile,
            )

            profile = (
                db.query(StudentProfile)
                .filter(
                    StudentProfile.user_id
                    == student.id
                )
                .first()
            )

            if (
                profile
                and profile.full_name
            ):
                student_name = (
                    profile.full_name
                )

        # ---------------------------------------------
        # Verified
        # ---------------------------------------------

        if (
            verification.status
            == "verified"
        ):

            activities.append(
                {
                    "id": (
                        100000
                        + verification.id
                    ),
                    "type": "verification",
                    "title": "Verified an experience",
                    "message": (
                        f'Verified "{experience_name}" '
                        f"experience submitted by "
                        f"{student_name}."
                    ),
                    "description": (
                        verification.feedback
                        or verification.comment
                        or None
                    ),
                    "created_at": safe_datetime(
                        verification.updated_at
                        or verification.created_at
                    ),
                }
            )

        # ---------------------------------------------
        # Rejected
        # ---------------------------------------------

        elif (
            verification.status
            == "rejected"
        ):

            activities.append(
                {
                    "id": (
                        100000
                        + verification.id
                    ),
                    "type": "rejection",
                    "title": "Rejected an experience",
                    "message": (
                        f'Rejected "{experience_name}" '
                        f"experience submitted by "
                        f"{student_name}."
                    ),
                    "description": (
                        verification.feedback
                        or verification.comment
                        or None
                    ),
                    "created_at": safe_datetime(
                        verification.updated_at
                        or verification.created_at
                    ),
                }
            )

    # =====================================================
    # 3. ENDORSEMENT ACTIVITY
    # =====================================================

    endorsements = (
        db.query(Endorsement)
        .filter(
            Endorsement.mentor_id
            == current_user.id,
        )
        .order_by(
            Endorsement.updated_at.desc()
        )
        .all()
    )

    for endorsement in endorsements:

        student = (
            db.query(User)
            .filter(
                User.id
                == endorsement.student_id,
                User.role == "student",
            )
            .first()
        )

        student_name = "Student"

        if student:
            from app.models.student_profile import (
                StudentProfile,
            )

            profile = (
                db.query(StudentProfile)
                .filter(
                    StudentProfile.user_id
                    == student.id
                )
                .first()
            )

            if (
                profile
                and profile.full_name
            ):
                student_name = (
                    profile.full_name
                )

        item_name = (
            endorsement.item_name
            or "item"
        )

        # ---------------------------------------------
        # Endorsed
        # ---------------------------------------------

        if (
            endorsement.status
            in [
                "endorsed",
                "approved",
                "accepted",
            ]
            or endorsement.is_endorsed
        ):

            if (
                endorsement.item_type
                == "skill"
            ):
                action_text = (
                    "Endorsed a skill"
                )
            else:
                action_text = (
                    "Endorsed a project"
                )

            activities.append(
                {
                    "id": (
                        200000
                        + endorsement.id
                    ),
                    "type": "endorsement",
                    "title": action_text,
                    "message": (
                        f'Endorsed "{item_name}" '
                        f"for {student_name}."
                    ),
                    "description": (
                        endorsement.mentor_comment
                        or endorsement.message
                        or None
                    ),
                    "created_at": safe_datetime(
                        endorsement.updated_at
                        or endorsement.created_at
                    ),
                }
            )

    # =====================================================
    # 4. SHORTLIST ACTIVITY
    # =====================================================

    shortlisted = (
        db.query(ShortlistedCandidate)
        .filter(
            ShortlistedCandidate.professional_id
            == current_user.id,
        )
        .order_by(
            ShortlistedCandidate.shortlisted_at.desc()
        )
        .all()
    )

    for shortlist in shortlisted:

        student = (
            db.query(User)
            .filter(
                User.id
                == shortlist.student_id,
                User.role == "student",
            )
            .first()
        )

        student_name = "Candidate"

        if student:
            from app.models.student_profile import (
                StudentProfile,
            )

            profile = (
                db.query(StudentProfile)
                .filter(
                    StudentProfile.user_id
                    == student.id
                )
                .first()
            )

            if (
                profile
                and profile.full_name
            ):
                student_name = (
                    profile.full_name
                )

        opportunity = (
            db.query(Opportunity)
            .filter(
                Opportunity.id
                == shortlist.opportunity_id
            )
            .first()
        )

        opportunity_title = (
            opportunity.title
            if opportunity
            and opportunity.title
            else "an opportunity"
        )

        activities.append(
            {
                "id": (
                    300000
                    + shortlist.id
                ),
                "type": "shortlist",
                "title": "Shortlisted a candidate",
                "message": (
                    f"Shortlisted {student_name} "
                    f"for "
                    f'"{opportunity_title}".'
                ),
                "description": None,
                "created_at": safe_datetime(
                    shortlist.shortlisted_at
                ),
            }
        )

    # =====================================================
    # 5. JOB CALL / OPPORTUNITY ACTIVITY
    # =====================================================

    opportunities = (
        db.query(Opportunity)
        .filter(
            Opportunity.professional_id
            == current_user.id,
        )
        .order_by(
            Opportunity.created_at.desc()
        )
        .all()
    )

    for opportunity in opportunities:

        company_name = (
            opportunity.company
            if opportunity.company
            else "a company"
        )

        opportunity_title = (
            opportunity.title
            if opportunity.title
            else "job opportunity"
        )

        activities.append(
            {
                "id": (
                    400000
                    + opportunity.id
                ),
                "type": "job_call",
                "title": "Created a job call",
                "message": (
                    f'Created "{opportunity_title}" '
                    f"at {company_name}."
                ),
                "description": None,
                "created_at": safe_datetime(
                    opportunity.created_at
                ),
            }
        )

    # =====================================================
    # 6. SORT ALL ACTIVITIES
    # =====================================================

    def activity_sort_key(activity):
        value = activity.get(
            "created_at"
        )

        if not value:
            return ""

        return value

    activities.sort(
        key=activity_sort_key,
        reverse=True,
    )

    # =====================================================
    # Return
    # =====================================================

    return {
        "activities": activities,
        "total": len(activities),
    }