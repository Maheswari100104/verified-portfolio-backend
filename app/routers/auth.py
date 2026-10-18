import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.mentor_profile import MentorProfile
from app.models.password_reset import PasswordResetToken

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ResetPasswordRequest,
)

from app.core.security import create_access_token
from app.core.dependencies import get_current_user

# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# Password Hashing
# =========================================================

password_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


# =========================================================
# Register
# =========================================================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Clean input
    # -----------------------------------------------------

    full_name = request.full_name.strip()
    email = request.email.strip().lower()
    role = request.role.strip().lower()

    # -----------------------------------------------------
    # Validate full name
    # -----------------------------------------------------

    if len(full_name) < 3:
        raise HTTPException(
            status_code=400,
            detail="Full name must contain at least 3 characters",
        )

    # -----------------------------------------------------
    # Validate password
    # -----------------------------------------------------

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )

    # -----------------------------------------------------
    # Validate role
    # -----------------------------------------------------

    allowed_roles = {
        "student",
        "mentor",
        "recruiter",
    }

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    # -----------------------------------------------------
    # Check whether email already exists
    # -----------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    # -----------------------------------------------------
    # Hash password
    # -----------------------------------------------------

    hashed_password = password_context.hash(
        request.password
    )

    # -----------------------------------------------------
    # Create User
    # -----------------------------------------------------

    user = User(
        email=email,
        password_hash=hashed_password,
        role=role,
        is_active=True,
    )

    db.add(user)

    try:
        # -------------------------------------------------
        # Flush User
        # -------------------------------------------------
        # This sends the INSERT to PostgreSQL and gives
        # us the generated user.id without committing yet.

        db.flush()

        # -------------------------------------------------
        # Create StudentProfile
        # -------------------------------------------------
        # At registration we currently store only the
        # full name. The remaining profile information will
        # be filled in through the portfolio builder.

        if role == "student":
            student_profile = StudentProfile(
                user_id=user.id,
                full_name=full_name,
            )

            db.add(student_profile)

        # -------------------------------------------------
        # Commit User + StudentProfile together
        # -------------------------------------------------

        db.commit()

        # Refresh User so generated values are available
        db.refresh(user)

    except Exception:
        # -------------------------------------------------
        # Roll back the entire transaction
        # -------------------------------------------------

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create account",
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Account created successfully",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }

# =========================================================
# Login
# =========================================================

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Find user by email
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    # -----------------------------------------------------
    # Check user exists
    # -----------------------------------------------------

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # -----------------------------------------------------
    # Check account is active
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account is inactive",
        )

    # -----------------------------------------------------
    # Verify password
    # -----------------------------------------------------

    password_valid = password_context.verify(
        request.password,
        user.password_hash,
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # -----------------------------------------------------
    # Create JWT access token
    # -----------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    # -----------------------------------------------------
    # Successful login
    # -----------------------------------------------------

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }

# =========================================================
# Get Current Logged-In User
# =========================================================




@router.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }
# =========================================================
# Forgot Password
# =========================================================

@router.post("/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Clean email
    # -----------------------------------------------------

    email = email.strip().lower()

    # -----------------------------------------------------
    # Find user by email
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # -----------------------------------------------------
    # Do not reveal whether email exists
    # -----------------------------------------------------

    if not user:
        return {
            "message": (
                "If the email is registered, "
                "a password reset link has been generated."
            )
        }

    # -----------------------------------------------------
    # Generate secure random token
    # -----------------------------------------------------

    raw_token = secrets.token_urlsafe(32)

    # -----------------------------------------------------
    # Hash token before storing it
    # -----------------------------------------------------

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    # -----------------------------------------------------
    # Token expires after 30 minutes
    # -----------------------------------------------------

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    # -----------------------------------------------------
    # Create reset token
    # -----------------------------------------------------

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False,
    )

    db.add(reset_token)

    try:
        db.commit()
        db.refresh(reset_token)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create password reset request",
        )

    # -----------------------------------------------------
    # TEMPORARY DEVELOPMENT RESPONSE
    # -----------------------------------------------------
    # Later the token will be sent through email.

    return {
        "message": (
            "If the email is registered, "
            "a password reset link has been generated."
        ),
        "reset_token": raw_token,
    }


# =========================================================
# Reset Password
# =========================================================

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Validate password
    # -----------------------------------------------------

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )

    # -----------------------------------------------------
    # Hash the token received from the user
    # -----------------------------------------------------

    token_hash = hashlib.sha256(
        request.token.encode()
    ).hexdigest()

    # -----------------------------------------------------
    # Find matching reset token
    # -----------------------------------------------------

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash
        )
        .first()
    )

    # -----------------------------------------------------
    # Token doesn't exist
    # -----------------------------------------------------

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid password reset token",
        )

    # -----------------------------------------------------
    # Check whether token was already used
    # -----------------------------------------------------

    if reset_token.used:
        raise HTTPException(
            status_code=400,
            detail="Password reset token has already been used",
        )

    # -----------------------------------------------------
    # Check token expiration
    # -----------------------------------------------------

    if reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Password reset token has expired",
        )

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.id == reset_token.user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # -----------------------------------------------------
    # Hash new password using Argon2
    # -----------------------------------------------------

    user.password_hash = password_context.hash(
        request.new_password
    )

    # -----------------------------------------------------
    # Mark reset token as used
    # -----------------------------------------------------

    reset_token.used = True

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to reset password",
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Password reset successfully",
    }