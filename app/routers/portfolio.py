
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.education_verification import EducationVerification


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


# =========================================================
# STUDENT-ONLY CHECK
# =========================================================

def verify_student(current_user: User):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can manage portfolios.",
        )


# =========================================================
# HELPER - SAFE JSON LOAD
# =========================================================

def safe_json_load(value, default):
    """
    Safely convert database JSON text into Python data.
    """
    if not value:
        return default

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


# =========================================================
# HELPER - EDUCATION VERIFICATION STATUS
# =========================================================

def attach_education_verification_status(education_list, db):
    """
    Attach the backend education verification status to each
    education entry returned by the portfolio API.

    Expected education entry ID keys:
        - id
        - education_id

    The ID must match educations.id and
    education_verifications.education_id.

    Uploaded documents and OCR text are never returned.
    """

    if not isinstance(education_list, list):
        return []

    education_ids = set()

    for item in education_list:
        if not isinstance(item, dict):
            continue

        raw_id = item.get("education_id")

        if raw_id is None:
            raw_id = item.get("id")

        try:
            if raw_id is not None:
                education_ids.add(int(raw_id))
        except (ValueError, TypeError):
            continue

    status_by_education_id = {}

    if education_ids:
        verifications = (
            db.query(
                EducationVerification.education_id,
                EducationVerification.status,
            )
            .filter(
                EducationVerification.education_id.in_(
                    list(education_ids)
                )
            )
            .all()
        )

        status_by_education_id = {
            row.education_id: row.status
            for row in verifications
        }

    result = []

    for item in education_list:
        if not isinstance(item, dict):
            result.append(item)
            continue

        raw_id = item.get("education_id")

        if raw_id is None:
            raw_id = item.get("id")

        try:
            education_id = (
                int(raw_id) if raw_id is not None else None
            )
        except (ValueError, TypeError):
            education_id = None

        status = status_by_education_id.get(
            education_id,
            "NOT_SUBMITTED",
        )

        # Return the education data plus the backend status.
        # Do not include document bytes or OCR contents.
        result.append({
            **item,
            "verificationStatus": status,
            "verification_status": status,
        })

    return result


# =========================================================
# PUBLISH PORTFOLIO
# =========================================================

@router.post("/publish")
def publish_portfolio(
    portfolio_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save/update the student's portfolio and publish it.
    """

    verify_student(current_user)

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == current_user.id
        )
        .first()
    )

    if not portfolio:
        portfolio = Portfolio(
            user_id=current_user.id
        )
        db.add(portfolio)

    # Store portfolio sections.
    portfolio.personal = json.dumps(
        portfolio_data.get("personal", {})
    )

    portfolio.education = json.dumps(
        portfolio_data.get("education", [])
    )

    portfolio.skills = json.dumps(
        portfolio_data.get("skills", [])
    )

    portfolio.projects = json.dumps(
        portfolio_data.get("projects", [])
    )

    portfolio.experience = json.dumps(
        portfolio_data.get("experience", [])
    )

    portfolio.certificates = json.dumps(
        portfolio_data.get("certificates", [])
    )

    portfolio.achievements = json.dumps(
        portfolio_data.get("achievements", [])
    )

    portfolio.languages = json.dumps(
        portfolio_data.get("languages", [])
    )

    portfolio.portfolio_template = portfolio_data.get(
        "portfolioTemplate",
        "Academic",
    )

    portfolio.is_published = True
    portfolio.public_slug = f"student-{current_user.id}"

    try:
        db.commit()
        db.refresh(portfolio)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to publish portfolio.",
        )

    return {
        "message": "Portfolio published successfully.",
        "portfolio_id": portfolio.id,
        "public_slug": portfolio.public_slug,
        "public_url": f"/portfolio/public/{portfolio.public_slug}",
        "portfolio_template": portfolio.portfolio_template,
    }


# =========================================================
# GET MY PORTFOLIO
# =========================================================

@router.get("/me")
def get_my_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the currently logged-in student's portfolio,
    including education verification status.
    """

    verify_student(current_user)

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == current_user.id
        )
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found.",
        )

    education = safe_json_load(
        portfolio.education,
        [],
    )

    education = attach_education_verification_status(
        education,
        db,
    )

    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,

        "personal": safe_json_load(
            portfolio.personal,
            {},
        ),

        "education": education,

        "skills": safe_json_load(
            portfolio.skills,
            [],
        ),

        "projects": safe_json_load(
            portfolio.projects,
            [],
        ),

        "experience": safe_json_load(
            portfolio.experience,
            [],
        ),

        "certificates": safe_json_load(
            portfolio.certificates,
            [],
        ),

        "achievements": safe_json_load(
            portfolio.achievements,
            [],
        ),

        "languages": safe_json_load(
            portfolio.languages,
            [],
        ),

        "portfolio_template": portfolio.portfolio_template,
        "is_published": portfolio.is_published,
        "public_slug": portfolio.public_slug,

        "final_resume": {
            "summary": portfolio.resume_summary,
            "source_signature": portfolio.resume_source_signature,
            "saved_at": portfolio.resume_saved_at,
            "is_saved": bool(
                portfolio.resume_summary
                and portfolio.resume_saved_at
            ),
        },
    }


# =========================================================
# SAVE FINAL RESUME
# =========================================================

@router.put("/final-resume")
def save_final_resume(
    resume_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save the student's final AI-generated resume.
    """

    verify_student(current_user)

    summary = resume_data.get("summary")
    source_signature = resume_data.get("source_signature")
    saved_at = resume_data.get("saved_at")

    if not summary or not str(summary).strip():
        raise HTTPException(
            status_code=400,
            detail="Resume summary is required.",
        )

    if not source_signature or not str(source_signature).strip():
        raise HTTPException(
            status_code=400,
            detail="Resume source signature is required.",
        )

    if not saved_at or not str(saved_at).strip():
        raise HTTPException(
            status_code=400,
            detail="Resume saved timestamp is required.",
        )

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == current_user.id
        )
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail=(
                "Portfolio not found. "
                "Please create your portfolio first."
            ),
        )

    portfolio.resume_summary = str(summary).strip()
    portfolio.resume_source_signature = str(source_signature)
    portfolio.resume_saved_at = str(saved_at)

    try:
        db.commit()
        db.refresh(portfolio)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the final resume.",
        )

    return {
        "message": "Final resume saved successfully.",
        "portfolio_id": portfolio.id,
        "resume": {
            "summary": portfolio.resume_summary,
            "source_signature": portfolio.resume_source_signature,
            "saved_at": portfolio.resume_saved_at,
            "is_saved": True,
        },
    }


# =========================================================
# PUBLIC PORTFOLIO
# =========================================================

@router.get("/public/{public_slug}")
def get_public_portfolio(
    public_slug: str,
    db: Session = Depends(get_db),
):
    """
    Public endpoint.

    No login is required.
    Only published portfolios can be viewed.

    Education verification status is included, but uploaded
    education documents and OCR contents remain private.
    """

    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.public_slug == public_slug,
            Portfolio.is_published.is_(True),
        )
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Published portfolio not found.",
        )

    student = (
        db.query(User)
        .filter(
            User.id == portfolio.user_id
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    education = safe_json_load(
        portfolio.education,
        [],
    )

    education = attach_education_verification_status(
        education,
        db,
    )

    return {
        "student": {
            "id": student.id,
            "email": student.email,
        },

        "portfolio": {
            "id": portfolio.id,

            "personal": safe_json_load(
                portfolio.personal,
                {},
            ),

            "education": education,

            "skills": safe_json_load(
                portfolio.skills,
                [],
            ),

            "projects": safe_json_load(
                portfolio.projects,
                [],
            ),

            "experience": safe_json_load(
                portfolio.experience,
                [],
            ),

            "certificates": safe_json_load(
                portfolio.certificates,
                [],
            ),

            "achievements": safe_json_load(
                portfolio.achievements,
                [],
            ),

            "languages": safe_json_load(
                portfolio.languages,
                [],
            ),

            "portfolio_template": portfolio.portfolio_template,
            "public_slug": portfolio.public_slug,
        },
    }
