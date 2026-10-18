from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.education import Education
from app.models.education_verification import EducationVerification
from app.models.student_skill import StudentSkill
from app.models.project import Project
from app.models.experience import Experience
from app.models.certificate import Certificate
from app.models.achievement import Achievement
from app.models.language import Language
from app.models.mentor_student import MentorStudent
from app.models.project_verification import ProjectVerification


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/student/dashboard",
    tags=["Student Dashboard"],
)


# =========================================================
# GET STUDENT DASHBOARD
# =========================================================

@router.get("/")
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # =====================================================
    # STUDENT-ONLY
    # =====================================================

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access the student dashboard.",
        )

    # =====================================================
    # FIND STUDENT PROFILE
    # =====================================================

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
            detail="Student profile not found.",
        )

    # =====================================================
    # PROFILE
    # =====================================================

    profile_photo_url = None

    if profile.profile_photo:
        profile_photo_url = (
            "http://127.0.0.1:8000"
            "/student/profile/me/photo"
        )

    student_profile = {
        "id": profile.id,
        "user_id": current_user.id,
        "full_name": profile.full_name,
        "email": current_user.email,
        "phone": profile.phone,
        "location": profile.location,
        "headline": profile.headline,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "website": profile.website,
        "about": profile.about,
        "profile_photo_url": profile_photo_url,
    }

    # =====================================================
    # EDUCATION
    # =====================================================

    education_records = (
        db.query(Education)
        .filter(
            Education.student_profile_id == profile.id
        )
        .order_by(
            Education.created_at.desc()
        )
        .all()
    )

    education_data = []

    for education in education_records:

        verification = (
            db.query(EducationVerification)
            .filter(
                EducationVerification.education_id
                == education.id
            )
            .first()
        )

        if verification:
            verification_status = verification.status
            verification_message = (
                verification.verification_message
            )
            checked_at = verification.checked_at
        else:
            verification_status = "NOT_SUBMITTED"
            verification_message = None
            checked_at = None

        education_data.append(
            {
                "id": education.id,
                "institution": education.institution,
                "degree": education.degree,
                "field_of_study": education.field_of_study,
                "start_date": education.start_date,
                "end_date": education.end_date,
                "is_current": education.is_current,
                "grade": education.grade,
                "description": education.description,

                "verification": {
                    "status": verification_status,
                    "message": verification_message,
                    "checked_at": checked_at,
                },
            }
        )

    education_count = len(education_records)

    # =====================================================
    # SKILLS
    # =====================================================

    skills_count = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # PROJECTS
    # =====================================================

    projects_count = (
        db.query(Project)
        .filter(
            Project.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # EXPERIENCE
    # =====================================================

    experience_count = (
        db.query(Experience)
        .filter(
            Experience.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # CERTIFICATES
    # =====================================================

    certificates_count = (
        db.query(Certificate)
        .filter(
            Certificate.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # ACHIEVEMENTS
    # =====================================================

    achievements_count = (
        db.query(Achievement)
        .filter(
            Achievement.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # LANGUAGES
    # =====================================================

    languages_count = (
        db.query(Language)
        .filter(
            Language.student_profile_id == profile.id
        )
        .count()
    )

    # =====================================================
    # MENTOR CONNECTION
    # =====================================================

    mentor_relationship = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.student_id == current_user.id,
            MentorStudent.is_active == True,
        )
        .order_by(
            MentorStudent.created_at.desc()
        )
        .first()
    )

    mentor_status = None
    mentor_id = None

    if mentor_relationship:
        mentor_status = mentor_relationship.status
        mentor_id = mentor_relationship.mentor_id

    # =====================================================
    # PROJECT VERIFICATIONS
    # =====================================================

    verification_records = (
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

    total_verification_requests = len(
        verification_records
    )

    pending_verifications = sum(
        1
        for item in verification_records
        if item.status == "pending"
    )

    verified_projects = sum(
        1
        for item in verification_records
        if item.status == "verified"
    )

    rejected_projects = sum(
        1
        for item in verification_records
        if item.status == "rejected"
    )

    # =====================================================
    # PROFILE COMPLETION
    # =====================================================

    profile_fields = [
        profile.full_name,
        profile.phone,
        profile.location,
        profile.headline,
        profile.about,
        profile.linkedin,
        profile.github,
        profile.website,
    ]

    completed_profile_fields = sum(
        1
        for field in profile_fields
        if field and str(field).strip()
    )

    total_profile_fields = len(
        profile_fields
    )

    profile_completion = round(
        (
            completed_profile_fields
            / total_profile_fields
        )
        * 100
    )

    # =====================================================
    # PORTFOLIO COMPLETION
    # =====================================================

    portfolio_sections = [
        education_count > 0,
        skills_count > 0,
        projects_count > 0,
        experience_count > 0,
        certificates_count > 0,
        achievements_count > 0,
        languages_count > 0,
    ]

    completed_sections = sum(
        1
        for section in portfolio_sections
        if section
    )

    total_sections = len(
        portfolio_sections
    )

    portfolio_completion = round(
        (
            completed_sections
            / total_sections
        )
        * 100
    )

    # =====================================================
    # RECENT VERIFICATION ACTIVITY
    # =====================================================

    verification_activity = []

    for item in verification_records[:5]:

        project = (
            db.query(Project)
            .filter(
                Project.id == item.project_id
            )
            .first()
        )

        verification_activity.append(
    {
        "id": item.id,
        "project_id": item.project_id,
        "project_title": (
            project.title
            if project
            else "Project"
        ),
        "status": item.status,

        # =================================================
        # Mentor Rating
        # =================================================

        "rating": item.rating,

        # =================================================
        # Mentor Feedback
        # =================================================

        "feedback": item.feedback,

        # =================================================
        # Verification Comment
        # =================================================

        "comment": item.comment,

        "is_verified": item.is_verified,

        "verified_at": item.verified_at,

        "created_at": item.created_at,

        "updated_at": item.updated_at,
    }
)
    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {
        # -------------------------------------------------
        # Student
        # -------------------------------------------------

        "student": student_profile,

        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        "statistics": {
            "education": education_count,
            "skills": skills_count,
            "projects": projects_count,
            "experience": experience_count,
            "certificates": certificates_count,
            "achievements": achievements_count,
            "languages": languages_count,
        },

        # -------------------------------------------------
        # Education + Verification
        # -------------------------------------------------

        "education": education_data,

        # -------------------------------------------------
        # Profile Completion
        # -------------------------------------------------

        "profile_completion": {
            "percentage": profile_completion,
            "completed": completed_profile_fields,
            "total": total_profile_fields,
        },

        # -------------------------------------------------
        # Portfolio Completion
        # -------------------------------------------------

        "portfolio_completion": {
            "percentage": portfolio_completion,
            "completed": completed_sections,
            "total": total_sections,
        },

        # -------------------------------------------------
        # Mentor
        # -------------------------------------------------

        "mentor": {
            "status": mentor_status,
            "mentor_id": mentor_id,
        },

        # -------------------------------------------------
        # Project Verification
        # -------------------------------------------------

        "verification": {
            "total_requests": total_verification_requests,
            "pending": pending_verifications,
            "verified": verified_projects,
            "rejected": rejected_projects,
        },

        # -------------------------------------------------
        # Verification Activity
        # -------------------------------------------------

        "verification_activity": verification_activity,
    }