from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

import traceback

from app.core.dependencies import get_current_user
from app.database.connection import get_db

from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.opportunity_interest import OpportunityInterest
from app.models.shortlisted_candidate import ShortlistedCandidate
from app.models.student_profile import StudentProfile
from app.models.portfolio import Portfolio
from app.models.notification import Notification

from app.services.email_service import send_shortlist_email


router = APIRouter(
    prefix="/shortlisted",
    tags=["Shortlisted Candidates"],
)


# =========================================================
# SHORTLIST A CANDIDATE
# IT PROFESSIONAL ONLY
# =========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def shortlist_candidate(
    opportunity_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # Check role
    # -----------------------------------------------------

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can shortlist candidates",
        )

    # -----------------------------------------------------
    # Check opportunity ownership
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Check whether student showed interest
    # -----------------------------------------------------

    interest = (
        db.query(OpportunityInterest)
        .filter(
            OpportunityInterest.opportunity_id == opportunity_id,
            OpportunityInterest.student_id == student_id,
        )
        .first()
    )

    if not interest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student has not shown interest in this opportunity",
        )

    # -----------------------------------------------------
    # Get student
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # -----------------------------------------------------
    # Get student profile
    # -----------------------------------------------------

    student_profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == student_id
        )
        .first()
    )

    # -----------------------------------------------------
    # Check if already shortlisted
    # -----------------------------------------------------

    existing_shortlist = (
        db.query(ShortlistedCandidate)
        .filter(
            ShortlistedCandidate.professional_id == current_user.id,
            ShortlistedCandidate.opportunity_id == opportunity_id,
            ShortlistedCandidate.student_id == student_id,
        )
        .first()
    )

    if existing_shortlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate is already shortlisted",
        )

    # -----------------------------------------------------
    # Create shortlist record
    # -----------------------------------------------------

    shortlist = ShortlistedCandidate(
        professional_id=current_user.id,
        opportunity_id=opportunity_id,
        student_id=student_id,
        status="shortlisted",
    )

    db.add(shortlist)

    # -----------------------------------------------------
    # Update interest status
    #
    # Student remains in Interested Students.
    # Their status changes to "shortlisted".
    # -----------------------------------------------------

    interest.status = "shortlisted"

    # -----------------------------------------------------
    # Prepare opportunity information
    # -----------------------------------------------------

    company_name = (
        opportunity.company
        if opportunity.company
        else "the company"
    )

    opportunity_title = (
        opportunity.title
        if opportunity.title
        else "this opportunity"
    )

    # -----------------------------------------------------
    # Prepare company contact details
    # -----------------------------------------------------

    company_website = (
        opportunity.company_website
        if opportunity.company_website
        else None
    )

    company_phone = (
        opportunity.company_phone
        if opportunity.company_phone
        else None
    )

    company_email = (
        opportunity.company_email
        if opportunity.company_email
        else None
    )

    # -----------------------------------------------------
    # Prepare candidate name
    # -----------------------------------------------------

    candidate_name = (
        student_profile.full_name
        if student_profile and student_profile.full_name
        else "Candidate"
    )

    # -----------------------------------------------------
    # Create student notification
    # -----------------------------------------------------

    notification = Notification(
        student_id=student_id,
        sender_id=current_user.id,
        opportunity_id=opportunity_id,
        type="shortlist",
        title="You've been shortlisted!",
        message=(
            f"Your profile has been shortlisted for "
            f"{opportunity_title} at {company_name}. "
            f"Please check your opportunity details for "
            f"the next steps."
        ),
        is_read=False,
    )

    db.add(notification)

    # -----------------------------------------------------
    # Save all database changes together
    #
    # 1. Shortlist record
    # 2. Interest status
    # 3. Student notification
    #
    # Email is intentionally sent AFTER commit.
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(shortlist)
        db.refresh(notification)

    except Exception as error:

        # Roll back failed transaction
        db.rollback()

        # -------------------------------------------------
        # PRINT ACTUAL ERROR TO FASTAPI TERMINAL
        # -------------------------------------------------

        print("\n")
        print("==============================================")
        print("SHORTLIST ERROR")
        print("==============================================")
        print("Error type:")
        print(type(error).__name__)
        print()
        print("Error message:")
        print(str(error))
        print()
        print("Full traceback:")
        traceback.print_exc()
        print("==============================================")
        print("\n")

        # Return the actual error to frontend as well
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to shortlist candidate: {str(error)}",
        )

    # =====================================================
    # SEND SHORTLIST EMAIL
    # =====================================================

    email_sent = False

    try:

        email_sent = send_shortlist_email(
            candidate_email=student.email,
            candidate_name=candidate_name,
            opportunity_title=opportunity_title,
            company_name=company_name,
            company_website=company_website,
            company_phone=company_phone,
            company_email=company_email,
        )

    except Exception as error:

        # -------------------------------------------------
        # IMPORTANT:
        # Email failure should NOT undo the shortlist.
        # The database transaction has already committed.
        # -------------------------------------------------

        print("\n")
        print("==============================================")
        print("SHORTLIST EMAIL ERROR")
        print("==============================================")
        print(type(error).__name__)
        print(str(error))
        print()
        traceback.print_exc()
        print("==============================================")
        print("\n")

        email_sent = False

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Candidate shortlisted successfully",
        "shortlist_id": shortlist.id,
        "opportunity_id": shortlist.opportunity_id,
        "student_id": shortlist.student_id,
        "status": shortlist.status,
        "notification_id": notification.id,
        "email_sent": email_sent,
    }


# =========================================================
# GET SHORTLISTED CANDIDATES
# IT PROFESSIONAL ONLY
# =========================================================

@router.get("")
def get_shortlisted_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # Check role
    # -----------------------------------------------------

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can view shortlisted candidates",
        )

    # -----------------------------------------------------
    # Get current professional's shortlisted candidates
    # -----------------------------------------------------

    shortlisted = (
        db.query(ShortlistedCandidate)
        .filter(
            ShortlistedCandidate.professional_id == current_user.id
        )
        .order_by(
            ShortlistedCandidate.shortlisted_at.desc()
        )
        .all()
    )

    result = []

    for item in shortlisted:

        # -------------------------------------------------
        # Student
        # -------------------------------------------------

        student = (
            db.query(User)
            .filter(
                User.id == item.student_id
            )
            .first()
        )

        # -------------------------------------------------
        # Student Profile
        # -------------------------------------------------

        profile = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.user_id == item.student_id
            )
            .first()
        )

        # -------------------------------------------------
        # Opportunity
        # -------------------------------------------------

        opportunity = (
            db.query(Opportunity)
            .filter(
                Opportunity.id == item.opportunity_id
            )
            .first()
        )

        # -------------------------------------------------
        # Published Portfolio
        # -------------------------------------------------

        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.user_id == item.student_id,
                Portfolio.is_published.is_(True),
            )
            .first()
        )

        # -------------------------------------------------
        # Build response
        # -------------------------------------------------

        result.append(
            {
                "id": item.id,

                "student_id": item.student_id,

                "student_name": (
                    profile.full_name
                    if profile
                    else None
                ),

                "email": (
                    student.email
                    if student
                    else None
                ),

                "headline": (
                    profile.headline
                    if profile
                    else None
                ),

                "location": (
                    profile.location
                    if profile
                    else None
                ),

                "opportunity_id": item.opportunity_id,

                "opportunity_title": (
                    opportunity.title
                    if opportunity
                    else None
                ),

                "company": (
                    opportunity.company
                    if opportunity
                    else None
                ),

                "status": item.status,

                "shortlisted_at": item.shortlisted_at,

                "public_slug": (
                    portfolio.public_slug
                    if portfolio
                    else None
                ),
            }
        )

    return result


# =========================================================
# REMOVE FROM SHORTLIST
# IT PROFESSIONAL ONLY
# =========================================================

@router.delete(
    "/{shortlist_id}"
)
def remove_from_shortlist(
    shortlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # Check role
    # -----------------------------------------------------

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT professionals can remove shortlisted candidates",
        )

    # -----------------------------------------------------
    # Find shortlist
    # -----------------------------------------------------

    shortlist = (
        db.query(ShortlistedCandidate)
        .filter(
            ShortlistedCandidate.id == shortlist_id,
            ShortlistedCandidate.professional_id == current_user.id,
        )
        .first()
    )

    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlisted candidate not found",
        )

    # -----------------------------------------------------
    # Restore interest status
    #
    # Candidate remains interested.
    # Only shortlist status is removed.
    # -----------------------------------------------------

    interest = (
        db.query(OpportunityInterest)
        .filter(
            OpportunityInterest.opportunity_id
            == shortlist.opportunity_id,

            OpportunityInterest.student_id
            == shortlist.student_id,
        )
        .first()
    )

    if interest:
        interest.status = "interested"

    # -----------------------------------------------------
    # Delete shortlist
    # -----------------------------------------------------

    db.delete(shortlist)

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    try:

        db.commit()

    except Exception as error:

        db.rollback()

        # Print actual database error
        print("\n")
        print("==============================================")
        print("REMOVE SHORTLIST ERROR")
        print("==============================================")
        print(type(error).__name__)
        print(str(error))
        print()
        traceback.print_exc()
        print("==============================================")
        print("\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to remove candidate from shortlist: {str(error)}",
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Candidate removed from shortlist"
    }