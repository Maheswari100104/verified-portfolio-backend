import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.user import User
from app.models.mentor_student import MentorStudent
from app.models.student_profile import StudentProfile
from app.models.mentor_profile import MentorProfile
from app.models.experience import Experience
from app.models.education import Education
from app.models.student_skill import StudentSkill
from app.models.project import Project
from app.models.certificate import Certificate
from app.models.achievement import Achievement
from app.models.language import Language
from app.models.skill import Skill

# =========================================================
# Verification models
# =========================================================

from app.models.education_verification import EducationVerification
from app.models.project_verification import ProjectVerification
from app.models.experience_verification import ExperienceVerification

# =========================================================
# Opportunity models
# =========================================================

from app.models.opportunity import Opportunity
from app.models.opportunity_interest import OpportunityInterest
from app.models.shortlisted_candidate import ShortlistedCandidate

# =========================================================
# Portfolio
# =========================================================

from app.models.portfolio import Portfolio

# =========================================================
# Schemas
# =========================================================

from app.schemas.mentor_student import (
    MentorRequestCreate,
    MentorStudentResponse,
)

# =========================================================
# Authentication
# =========================================================

from app.core.dependencies import get_current_user


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/mentor-student",
    tags=["Mentor Student"],
)


# =========================================================
# Helper
# Verify Student Portfolio Access
# =========================================================

# Recruitment rule:
#
# If the student has shown interest in ANY opportunity,
# an IT Professional can view the student's portfolio.
#
# No mentor request is required.
# No mentor acceptance is required.
#
# =========================================================

def verify_student_portfolio_access(
    student_id: int,
    db: Session,
):
    interest = (
        db.query(OpportunityInterest)
        .filter(
            OpportunityInterest.student_id
            == student_id,
        )
        .first()
    )

    if interest:
        return True

    raise HTTPException(
        status_code=403,
        detail=(
            "This student's portfolio is available "
            "after showing interest in an opportunity."
        ),
    )


# =========================================================
# Student → Send Mentor Request
# =========================================================

@router.post(
    "/request",
    response_model=MentorStudentResponse,
)
def send_mentor_request(
    request: MentorRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can send mentor requests.",
        )

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
            detail="Mentor not found.",
        )

    if mentor.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot send a request to yourself.",
        )

    existing_request = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.mentor_id
            == mentor.id,
            MentorStudent.student_id
            == current_user.id,
        )
        .first()
    )

    if existing_request:

        if existing_request.status == "pending":
            raise HTTPException(
                status_code=409,
                detail="Mentor request is already pending.",
            )

        if existing_request.status == "accepted":
            raise HTTPException(
                status_code=409,
                detail=(
                    "You are already connected "
                    "with this mentor."
                ),
            )

        existing_request.status = "pending"
        existing_request.is_active = True

        try:
            db.commit()
            db.refresh(existing_request)

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail="Unable to send mentor request.",
            )

        return existing_request

    mentor_student = MentorStudent(
        mentor_id=mentor.id,
        student_id=current_user.id,
        status="pending",
        is_active=True,
    )

    db.add(mentor_student)

    try:
        db.commit()
        db.refresh(mentor_student)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to send mentor request.",
        )

    return mentor_student


# =========================================================
# Student → View My Mentor Requests
# =========================================================

@router.get(
    "/my-requests",
    response_model=list[MentorStudentResponse],
)
def get_my_mentor_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can view "
                "their mentor requests."
            ),
        )

    requests = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.student_id
            == current_user.id,
        )
        .order_by(
            MentorStudent.created_at.desc()
        )
        .all()
    )

    return requests


# =========================================================
# Student → View Accepted Mentors
# =========================================================

@router.get(
    "/my-mentors",
)
def get_my_accepted_mentors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can view "
                "their accepted mentors."
            ),
        )

    relationships = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.student_id
            == current_user.id,
            MentorStudent.status == "accepted",
            MentorStudent.is_active == True,
        )
        .order_by(
            MentorStudent.created_at.desc()
        )
        .all()
    )

    mentors = []

    for relationship in relationships:

        mentor_user = (
            db.query(User)
            .filter(
                User.id == relationship.mentor_id,
                User.role == "mentor",
                User.is_active == True,
            )
            .first()
        )

        if not mentor_user:
            continue

        mentor_profile = (
            db.query(MentorProfile)
            .filter(
                MentorProfile.user_id
                == mentor_user.id
            )
            .first()
        )

        mentors.append(
            {
                "id": mentor_user.id,

                "full_name": (
                    mentor_profile.full_name
                    if mentor_profile
                    else "Mentor"
                ),

                "email": mentor_user.email,

                "headline": (
                    mentor_profile.designation
                    if mentor_profile
                    else None
                ),

                "relationship_id": (
                    relationship.id
                ),
            }
        )

    return {
        "mentors": mentors,
        "total": len(mentors),
    }


# =========================================================
# Mentor → View Pending Requests
# =========================================================

@router.get(
    "/requests",
    response_model=list[MentorStudentResponse],
)
def get_mentor_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail="Only mentors can view mentor requests.",
        )

    requests = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "pending",
            MentorStudent.is_active == True,
        )
        .order_by(
            MentorStudent.created_at.desc()
        )
        .all()
    )

    return requests


# =========================================================
# Mentor → Accept Request
# =========================================================

@router.put(
    "/requests/{request_id}/accept",
    response_model=MentorStudentResponse,
)
def accept_mentor_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail="Only mentors can accept requests.",
        )

    mentor_student = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.id == request_id,
            MentorStudent.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not mentor_student:
        raise HTTPException(
            status_code=404,
            detail="Mentor request not found.",
        )

    if mentor_student.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This mentor request has "
                "already been processed."
            ),
        )

    mentor_student.status = "accepted"
    mentor_student.is_active = True

    try:
        db.commit()
        db.refresh(mentor_student)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to accept mentor request.",
        )

    return mentor_student


# =========================================================
# Mentor → Reject Request
# =========================================================

@router.put(
    "/requests/{request_id}/reject",
    response_model=MentorStudentResponse,
)
def reject_mentor_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail="Only mentors can reject requests.",
        )

    mentor_student = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.id == request_id,
            MentorStudent.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not mentor_student:
        raise HTTPException(
            status_code=404,
            detail="Mentor request not found.",
        )

    if mentor_student.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This mentor request has "
                "already been processed."
            ),
        )

    mentor_student.status = "rejected"
    mentor_student.is_active = False

    try:
        db.commit()
        db.refresh(mentor_student)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to reject mentor request.",
        )

    return mentor_student


# =========================================================
# Mentor Dashboard Statistics
# =========================================================

# =========================================================
# Mentor Dashboard Statistics
# =========================================================

@router.get(
    "/dashboard-stats",
)
def get_mentor_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # IT Professional only
    # -----------------------------------------------------

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can access "
                "dashboard statistics."
            ),
        )

    # =====================================================
    # 1. TOTAL CANDIDATES
    # =====================================================
    #
    # A candidate is a student who has shown interest
    # in at least one opportunity.
    #
    # DISTINCT prevents counting the same student more
    # than once if they showed interest in multiple
    # opportunities.
    # =====================================================

    candidate_count = (
        db.query(
            OpportunityInterest.student_id
        )
        .distinct()
        .count()
    )

    # =====================================================
    # 2. SHORTLISTED CANDIDATES
    # =====================================================
    #
    # Only count candidates shortlisted by the
    # currently logged-in IT professional.
    # =====================================================

    shortlisted_count = (
        db.query(
            ShortlistedCandidate
        )
        .filter(
            ShortlistedCandidate.professional_id
            == current_user.id
        )
        .count()
    )

    # =====================================================
    # 3. JOB CALLS
    # =====================================================
    #
    # Count opportunities created by the current
    # IT professional.
    # =====================================================

    job_call_count = (
        db.query(
            Opportunity
        )
        .filter(
            Opportunity.professional_id
            == current_user.id
        )
        .count()
    )

    # =====================================================
    # 4. JOB CALL RESPONSES
    # =====================================================
    #
    # Count students who showed interest in opportunities
    # created by this IT professional.
    # =====================================================

    job_call_response_count = (
        db.query(
            OpportunityInterest
        )
        .join(
            Opportunity,
            Opportunity.id
            == OpportunityInterest.opportunity_id
        )
        .filter(
            Opportunity.professional_id
            == current_user.id
        )
        .count()
    )

    # =====================================================
    # 5. SAVED CANDIDATES
    # =====================================================
    #
    # Saved-candidate functionality does not currently
    # have a dedicated backend model in this router.
    #
    # Keep this as 0 until the Saved Candidate feature
    # is implemented in the backend.
    # =====================================================

    saved_candidate_count = 0

    # =====================================================
    # 6. EXISTING MENTOR CONNECTION STATISTICS
    # =====================================================

    total_students = (
        db.query(
            MentorStudent
        )
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "accepted",
            MentorStudent.is_active == True,
        )
        .count()
    )

    pending_requests = (
        db.query(
            MentorStudent
        )
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "pending",
            MentorStudent.is_active == True,
        )
        .count()
    )

    # =====================================================
    # 7. RESPONSE
    # =====================================================

    return {
        # Existing mentor statistics
        "total_students": total_students,
        "pending_requests": pending_requests,
        "verified_portfolios": 0,
        "feedback_given": 0,

        # Hiring dashboard statistics
        "candidates": candidate_count,
        "shortlisted": shortlisted_count,
        "job_calls": job_call_count,
        "saved_candidates": saved_candidate_count,
        "job_call_responses": job_call_response_count,

        # Growth values are not calculated yet.
        "candidate_growth": 0,
        "shortlisted_growth": 0,
    }

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only mentors can access "
                "dashboard statistics."
            ),
        )

    total_students = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "accepted",
            MentorStudent.is_active == True,
        )
        .count()
    )

    pending_requests = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "pending",
            MentorStudent.is_active == True,
        )
        .count()
    )

    verified_portfolios = 0
    feedback_given = 0

    return {
        "total_students": total_students,
        "pending_requests": pending_requests,
        "verified_portfolios": verified_portfolios,
        "feedback_given": feedback_given,
    }


# =========================================================
# Mentor → View Connected Students
# =========================================================

@router.get(
    "/students",
)
def get_connected_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only mentors can view "
                "connected students."
            ),
        )

    relationships = (
        db.query(MentorStudent)
        .filter(
            MentorStudent.mentor_id
            == current_user.id,
            MentorStudent.status == "accepted",
            MentorStudent.is_active == True,
        )
        .order_by(
            MentorStudent.created_at.desc()
        )
        .all()
    )

    students = []

    for relationship in relationships:

        student_user = (
            db.query(User)
            .filter(
                User.id
                == relationship.student_id,
                User.role == "student",
            )
            .first()
        )

        if not student_user:
            continue

        student_profile = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.user_id
                == student_user.id
            )
            .first()
        )

        students.append(
            {
                "relationship_id": (
                    relationship.id
                ),

                "student_id": (
                    student_user.id
                ),

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

                "location": (
                    student_profile.location
                    if student_profile
                    else ""
                ),
            }
        )

    return {
        "students": students,
        "total": len(students),
    }


# =========================================================
# Mentor / IT Professional → View Candidates
# =========================================================

@router.get(
    "/candidates",
)
def get_candidates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can "
                "view candidates."
            ),
        )

    # -----------------------------------------------------
    # Students who showed interest in any opportunity
    # -----------------------------------------------------

    student_ids = (
        db.query(
            OpportunityInterest.student_id
        )
        .distinct()
        .all()
    )

    student_ids = [
        student_id
        for (student_id,) in student_ids
    ]

    if not student_ids:
        return {
            "candidates": [],
            "total": 0,
        }

    # -----------------------------------------------------
    # Active students
    # -----------------------------------------------------

    student_users = (
        db.query(User)
        .filter(
            User.id.in_(student_ids),
            User.role == "student",
            User.is_active == True,
        )
        .all()
    )

    candidates = []

    # -----------------------------------------------------
    # Build candidate data
    # -----------------------------------------------------

    for student_user in student_users:

        student_profile = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.user_id
                == student_user.id
            )
            .first()
        )

        if not student_profile:
            continue

        # =================================================
        # Skills
        # =================================================

        skill_records = (
            db.query(StudentSkill)
            .filter(
                StudentSkill.student_profile_id
                == student_profile.id
            )
            .all()
        )

        skills = []

        for skill_record in skill_records:

            skill_name = None

            if skill_record.skill_id:

                skill = (
                    db.query(Skill)
                    .filter(
                        Skill.id
                        == skill_record.skill_id
                    )
                    .first()
                )

                if skill:
                    skill_name = skill.name

            if not skill_name:
                skill_name = (
                    skill_record.custom_skill_name
                )

            if skill_name:
                skills.append(
                    {
                        "id": skill_record.id,
                        "name": skill_name,
                        "level": skill_record.level,
                    }
                )

        # =================================================
        # EDUCATION VERIFICATION
        # =================================================

        education_records = (
            db.query(Education)
            .filter(
                Education.student_profile_id
                == student_profile.id
            )
            .all()
        )

        education_status = "not_verified"

        if education_records:

            education_verified = False
            education_pending = False
            education_rejected = False

            for education in education_records:

                verification = (
                    db.query(
                        EducationVerification
                    )
                    .filter(
                        EducationVerification.education_id
                        == education.id
                    )
                    .first()
                )

                if not verification:
                    continue

                status = (
                    verification.status
                    or ""
                ).strip().lower()

                if status in ("verified", "matched"):
                    education_verified = True

                elif status in ("pending", "mismatch"):
                    education_pending = True

                elif status in ("rejected", "flagged"):
                    education_rejected = True

            if education_verified:
                education_status = "verified"

            elif education_pending:
                education_status = "pending"

            elif education_rejected:
                education_status = "rejected"

        # =================================================
        # PROJECT VERIFICATION
        # =================================================

        project_records = (
            db.query(Project)
            .filter(
                Project.student_profile_id
                == student_profile.id
            )
            .all()
        )

        project_status = "not_verified"

        if project_records:

            project_verified = False
            project_pending = False
            project_rejected = False

            for project in project_records:

                verification = (
                    db.query(
                        ProjectVerification
                    )
                    .filter(
                        ProjectVerification.project_id
                        == project.id
                    )
                    .order_by(
                        ProjectVerification.created_at.desc()
                    )
                    .first()
                )

                if not verification:
                    continue

                status = (
                    verification.status
                    or ""
                ).strip().lower()

                if (
                    status == "verified"
                    or verification.is_verified
                ):
                    project_verified = True

                elif status == "pending":
                    project_pending = True

                elif status == "rejected":
                    project_rejected = True

            if project_verified:
                project_status = "verified"

            elif project_pending:
                project_status = "pending"

            elif project_rejected:
                project_status = "rejected"

        # =================================================
        # EXPERIENCE VERIFICATION
        # =================================================

        experience_records = (
            db.query(Experience)
            .filter(
                Experience.student_profile_id
                == student_profile.id
            )
            .all()
        )

        experience_status = "not_verified"

        if experience_records:

            experience_verified = False
            experience_pending = False
            experience_rejected = False

            for experience in experience_records:

                verification = (
                    db.query(
                        ExperienceVerification
                    )
                    .filter(
                        ExperienceVerification.experience_id
                        == experience.id
                    )
                    .order_by(
                        ExperienceVerification.created_at.desc()
                    )
                    .first()
                )

                if not verification:
                    continue

                status = (
                    verification.status
                    or ""
                ).strip().lower()

                if (
                    status == "verified"
                    or verification.is_verified
                ):
                    experience_verified = True

                elif status == "pending":
                    experience_pending = True

                elif status == "rejected":
                    experience_rejected = True

            if experience_verified:
                experience_status = "verified"

            elif experience_pending:
                experience_status = "pending"

            elif experience_rejected:
                experience_status = "rejected"

        # =================================================
        # Candidate
        # =================================================

        candidates.append(
            {
                "id": student_user.id,

                "name": (
                    student_profile.full_name
                    or "Student"
                ),

                "email": student_user.email,

                "headline": (
                    student_profile.headline
                    or ""
                ),

                "location": (
                    student_profile.location
                    or ""
                ),

                "phone": (
                    student_profile.phone
                    or ""
                ),

                "linkedin": (
                    student_profile.linkedin
                    or ""
                ),

                "github": (
                    student_profile.github
                    or ""
                ),

                "website": (
                    student_profile.website
                    or ""
                ),

                "about": (
                    student_profile.about
                    or ""
                ),

                "skills": skills,

                "verification": {
                    "education": education_status,
                    "projects": project_status,
                    "experience": experience_status,
                },

                "shortlisted": False,
            }
        )

    return {
        "candidates": candidates,
        "total": len(candidates),
    }


# =========================================================
# Mentor → View Student Portfolio
# =========================================================

@router.get(
    "/students/{student_id}/portfolio",
)
def get_student_published_portfolio(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can view "
                "student portfolios."
            ),
        )

    # -----------------------------------------------------
    # Verify access
    # -----------------------------------------------------

    verify_student_portfolio_access(
        student_id=student_id,
        db=db,
    )

    # -----------------------------------------------------
    # Student
    # -----------------------------------------------------

    student_user = (
        db.query(User)
        .filter(
            User.id == student_id,
            User.role == "student",
            User.is_active == True,
        )
        .first()
    )

    if not student_user:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    # -----------------------------------------------------
    # Portfolio
    # -----------------------------------------------------

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == student_id,
        )
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found for this student.",
        )

    # -----------------------------------------------------
    # Published check
    # -----------------------------------------------------

    if not portfolio.is_published:
        raise HTTPException(
            status_code=404,
            detail=(
                "This student has not published "
                "their portfolio yet."
            ),
        )

    if not portfolio.public_slug:
        raise HTTPException(
            status_code=404,
            detail=(
                "Published portfolio URL "
                "is not available."
            ),
        )

    return {
        "student_id": student_user.id,

        "portfolio_id": portfolio.id,

        "is_published": (
            portfolio.is_published
        ),

        "public_slug": (
            portfolio.public_slug
        ),

        "portfolio_template": (
            portfolio.portfolio_template
        ),

        "portfolio_url": (
            f"/portfolio/{portfolio.public_slug}"
        ),
    }


# =========================================================
# Mentor → Find Mentor By Email
# =========================================================

@router.get(
    "/find-by-email",
)
def find_mentor_by_email(
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can search for mentors.",
        )

    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Mentor email is required.",
        )

    mentor_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.role == "mentor",
            User.is_active == True,
        )
        .first()
    )

    if not mentor_user:
        raise HTTPException(
            status_code=404,
            detail=(
                "No active mentor found "
                "with this email address."
            ),
        )

    if mentor_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "You cannot search for yourself "
                "as a mentor."
            ),
        )

    mentor_profile = (
        db.query(MentorProfile)
        .filter(
            MentorProfile.user_id
            == mentor_user.id
        )
        .first()
    )

    if not mentor_profile:
        raise HTTPException(
            status_code=404,
            detail="Mentor profile not found.",
        )

    return {
        "id": mentor_user.id,

        "full_name": (
            mentor_profile.full_name
            or "Mentor"
        ),

        "email": mentor_user.email,

        "headline": (
            mentor_profile.designation
            if mentor_profile.designation
            else None
        ),
    }


# =========================================================
# Mentor / IT Professional → View Student Final Resume
# =========================================================

@router.get(
    "/students/{student_id}/resume",
)
def get_student_resume(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the student's saved final resume.

    The resume is NOT generated again for the mentor.

    It uses the student's existing portfolio data and
    the AI-generated summary that the student saved from
    My Resume.
    """

    # -----------------------------------------------------
    # IT Professional / Mentor only
    # -----------------------------------------------------

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can view "
                "student resumes."
            ),
        )

    # -----------------------------------------------------
    # Verify candidate access
    # -----------------------------------------------------

    verify_student_portfolio_access(
        student_id=student_id,
        db=db,
    )

    # -----------------------------------------------------
    # Verify student
    # -----------------------------------------------------

    student = (
        db.query(User)
        .filter(
            User.id == student_id,
            User.role == "student",
            User.is_active == True,
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    # -----------------------------------------------------
    # Get student's portfolio
    # -----------------------------------------------------

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == student_id
        )
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found.",
        )

    # -----------------------------------------------------
    # Final resume check
    # -----------------------------------------------------

    if not portfolio.resume_summary:
        raise HTTPException(
            status_code=404,
            detail=(
                "This student has not saved "
                "a final resume yet."
            ),
        )

    # -----------------------------------------------------
    # Safe JSON parser
    # -----------------------------------------------------

    def parse_json(
        value,
        default,
    ):
        if not value:
            return default

        try:
            return json.loads(value)

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return default

    # -----------------------------------------------------
    # Decode portfolio sections
    # -----------------------------------------------------

    personal = parse_json(
        portfolio.personal,
        {},
    )

    education = parse_json(
        portfolio.education,
        [],
    )

    skills = parse_json(
        portfolio.skills,
        [],
    )

    projects = parse_json(
        portfolio.projects,
        [],
    )

    experience = parse_json(
        portfolio.experience,
        [],
    )

    certificates = parse_json(
        portfolio.certificates,
        [],
    )

    achievements = parse_json(
        portfolio.achievements,
        [],
    )

    languages = parse_json(
        portfolio.languages,
        [],
    )

    # -----------------------------------------------------
    # Determine student name safely
    # -----------------------------------------------------

    student_name = (
        personal.get("fullName")
        or personal.get("name")
        or "Student"
    )

    # -----------------------------------------------------
    # Return final resume
    # -----------------------------------------------------

    return {
        "student_id": student.id,

        "student_name": student_name,

        "personal": personal,

        "education": education,

        "skills": skills,

        "projects": projects,

        "experience": experience,

        "certificates": certificates,

        "achievements": achievements,

        "languages": languages,

        # -------------------------------------------------
        # AI-generated final summary
        # -------------------------------------------------

        "resume_summary": (
            portfolio.resume_summary
        ),

        # -------------------------------------------------
        # Final resume metadata
        # -------------------------------------------------

        "resume_saved_at": (
            portfolio.resume_saved_at
        ),

        "resume_source_signature": (
            portfolio.resume_source_signature
        ),

        # -------------------------------------------------
        # Portfolio information
        # -------------------------------------------------

        "portfolio_template": (
            portfolio.portfolio_template
        ),

        "portfolio_id": portfolio.id,

        "is_published": (
            portfolio.is_published
        ),

        "public_slug": (
            portfolio.public_slug
        ),
    }