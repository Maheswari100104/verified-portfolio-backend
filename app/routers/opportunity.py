
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db

from app.models.opportunity import Opportunity
from app.models.opportunity_interest import OpportunityInterest
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.portfolio import Portfolio
from app.models.notification import Notification

from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityResponse,
)

from app.schemas.opportunity_interest import (
    OpportunityInterestResponse,
)


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


# =========================================================
# CREATE OPPORTUNITY
# IT PROFESSIONAL ONLY
# =========================================================

@router.post(
    "",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can post opportunities",
        )

    opportunity = Opportunity(
        professional_id=current_user.id,
        type=opportunity_data.type,
        title=opportunity_data.title,
        company=opportunity_data.company,
        company_website=opportunity_data.company_website,
        company_phone=opportunity_data.company_phone,
        company_email=opportunity_data.company_email,
        location=opportunity_data.location,
        work_mode=opportunity_data.work_mode,
        description=opportunity_data.description,
        required_skills=opportunity_data.required_skills,
        experience=opportunity_data.experience,
        eligibility=opportunity_data.eligibility,
        duration=opportunity_data.duration,
        deadline=opportunity_data.deadline,
        status="active",
    )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    return opportunity


# =========================================================
# GET MY OPPORTUNITIES
# IT PROFESSIONAL ONLY
# =========================================================

@router.get(
    "/my",
    response_model=list[OpportunityResponse],
)
def get_my_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can view their opportunities",
        )

    return (
        db.query(Opportunity)
        .filter(Opportunity.professional_id == current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )


# =========================================================
# GET ACTIVE OPPORTUNITIES
# STUDENT ONLY
# =========================================================

@router.get(
    "",
    response_model=list[OpportunityResponse],
)
def get_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view opportunities",
        )

    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.status == "active")
        .order_by(Opportunity.created_at.desc())
        .all()
    )

    result = []

    for opportunity in opportunities:
        interest = (
            db.query(OpportunityInterest)
            .filter(
                OpportunityInterest.opportunity_id == opportunity.id,
                OpportunityInterest.student_id == current_user.id,
            )
            .first()
        )

        result.append(
            {
                "id": opportunity.id,
                "professional_id": opportunity.professional_id,
                "type": opportunity.type,
                "title": opportunity.title,
                "company": opportunity.company,
                "company_website": opportunity.company_website,
                "company_phone": opportunity.company_phone,
                "company_email": opportunity.company_email,
                "location": opportunity.location,
                "work_mode": opportunity.work_mode,
                "description": opportunity.description,
                "required_skills": opportunity.required_skills,
                "experience": opportunity.experience,
                "eligibility": opportunity.eligibility,
                "duration": opportunity.duration,
                "deadline": opportunity.deadline,
                "status": opportunity.status,
                "created_at": opportunity.created_at,
                "interest_status": (
                    interest.status if interest else None
                ),
            }
        )

    return result


# =========================================================
# STUDENT SHOWS INTEREST
# CREATES NOTIFICATION FOR OPPORTUNITY OWNER
# =========================================================

@router.post(
    "/{opportunity_id}/interest",
    response_model=OpportunityInterestResponse,
    status_code=status.HTTP_201_CREATED,
)
def show_interest(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can show interest",
        )

    opportunity = (
        db.query(Opportunity)
        .filter(
            Opportunity.id == opportunity_id,
            Opportunity.status == "active",
        )
        .first()
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found or no longer active",
        )

    existing_interest = (
        db.query(OpportunityInterest)
        .filter(
            OpportunityInterest.opportunity_id == opportunity_id,
            OpportunityInterest.student_id == current_user.id,
        )
        .first()
    )

    if existing_interest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already shown interest in this opportunity",
        )

    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    student_name = (
        student_profile.full_name
        if student_profile and student_profile.full_name
        else current_user.email
    )

    interest = OpportunityInterest(
        opportunity_id=opportunity.id,
        student_id=current_user.id,
        status="interested",
    )

    notification = Notification(
        recipient_id=opportunity.professional_id,
        student_id=None,
        sender_id=current_user.id,
        opportunity_id=opportunity.id,
        type="opportunity_interest",
        title="New Candidate Interest",
        message=(
            f"{student_name} has expressed interest in your opportunity "
            f"'{opportunity.title}'. Review the candidate in CareerVault."
        ),
        is_read=False,
    )

    try:
        db.add(interest)
        db.add(notification)
        db.commit()
        db.refresh(interest)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register interest. Please try again.",
        )

    return interest


# =========================================================
# GET INTERESTED STUDENTS
# IT PROFESSIONAL ONLY
# =========================================================

@router.get(
    "/{opportunity_id}/interested",
    response_model=list[OpportunityInterestResponse],
)
def get_interested_students(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can view interested students",
        )

    opportunity = (
        db.query(Opportunity)
        .filter(
            Opportunity.id == opportunity_id,
            Opportunity.professional_id == current_user.id,
        )
        .first()
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    interests = (
        db.query(OpportunityInterest)
        .filter(
            OpportunityInterest.opportunity_id == opportunity_id
        )
        .order_by(OpportunityInterest.created_at.desc())
        .all()
    )

    result = []

    for interest in interests:
        student = (
            db.query(User)
            .filter(User.id == interest.student_id)
            .first()
        )

        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == interest.student_id)
            .first()
        )

        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.user_id == interest.student_id,
                Portfolio.is_published.is_(True),
            )
            .first()
        )

        skills = []

        if profile:
            for student_skill in profile.student_skills:
                if student_skill.skill:
                    skills.append(student_skill.skill.name)
                elif student_skill.custom_skill_name:
                    skills.append(student_skill.custom_skill_name)

        skills = list(dict.fromkeys(skills))

        result.append(
            {
                "id": interest.id,
                "opportunity_id": interest.opportunity_id,
                "student_id": interest.student_id,
                "student_name": (
                    profile.full_name if profile else None
                ),
                "email": student.email if student else None,
                "headline": profile.headline if profile else None,
                "location": profile.location if profile else None,
                "skills": skills,
                "status": interest.status,
                "ai_match_percentage": interest.ai_match_percentage,
                "created_at": interest.created_at,
                "public_slug": (
                    portfolio.public_slug if portfolio else None
                ),
            }
        )

    return result


# =========================================================
# DELETE OPPORTUNITY
# IT PROFESSIONAL ONLY
# =========================================================

@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_200_OK,
)
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can delete opportunities",
        )

    opportunity = (
        db.query(Opportunity)
        .filter(
            Opportunity.id == opportunity_id,
            Opportunity.professional_id == current_user.id,
        )
        .first()
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    from app.models.shortlisted_candidate import ShortlistedCandidate

    try:
        # Remove related interests
        db.query(OpportunityInterest).filter(
            OpportunityInterest.opportunity_id == opportunity_id
        ).delete(synchronize_session=False)

        # Remove shortlist records
        db.query(ShortlistedCandidate).filter(
            ShortlistedCandidate.opportunity_id == opportunity_id
        ).delete(synchronize_session=False)

        # Remove notifications related to this opportunity
        db.query(Notification).filter(
            Notification.opportunity_id == opportunity_id
        ).delete(synchronize_session=False)

        db.delete(opportunity)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete opportunity. Please try again.",
        )

    return {
        "message": "Opportunity deleted successfully",
        "opportunity_id": opportunity_id,
    }
