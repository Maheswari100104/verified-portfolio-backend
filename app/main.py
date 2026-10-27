from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine


# =========================================================
# MODELS
# =========================================================
# Import every model before create_all()
# so SQLAlchemy knows about every table.
# =========================================================

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.mentor_profile import MentorProfile

from app.models.education import Education
from app.models.experience import Experience

from app.models.student_skill import StudentSkill
from app.models.skill import Skill

from app.models.project import Project
from app.models.certificate import Certificate
from app.models.achievement import Achievement
from app.models.language import Language

from app.models.mentor_student import MentorStudent


# =========================================================
# PORTFOLIO MODEL
# =========================================================

from app.models.portfolio import Portfolio


# =========================================================
# VERIFICATION MODELS
# =========================================================

from app.models.education_verification import EducationVerification
from app.models.project_verification import ProjectVerification
from app.models.experience_verification import ExperienceVerification


# =========================================================
# ENDORSEMENT MODEL
# =========================================================

from app.models.endorsement import Endorsement


# =========================================================
# OPPORTUNITY MODELS
# =========================================================

from app.models.opportunity import Opportunity
from app.models.opportunity_interest import OpportunityInterest

from app.models.notification import Notification
# =========================================================
# SHORTLISTED CANDIDATE MODEL
# =========================================================

from app.models.shortlisted_candidate import ShortlistedCandidate


# =========================================================
# CREATE DATABASE TABLES
# =========================================================
# IMPORTANT:
# All SQLAlchemy models must be imported before this line.
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# ROUTERS
# =========================================================

from app.routers.auth import router as auth_router

from app.routers import student_profile
from app.routers import student_dashboard

from app.routers import education
from app.routers import experience

from app.routers import skills
from app.routers import projects
from app.routers import certificate
from app.routers import achievement
from app.routers import language

from app.routers import mentor
from app.routers import mentor_student

from app.routers import education_verification
from app.routers import project_verification
from app.routers import experience_verification

from app.routers import endorsement
from app.routers import opportunity

from app.routers import portfolio

from app.routers import ai_resume
from app.routers import hiring_activity

# =========================================================
# SHORTLISTED CANDIDATES ROUTER
# =========================================================

from app.routers import shortlisted
from app.routers import notifications

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="CareerVault Builder API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://career-vault-2026.pages.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =========================================================
# AUTHENTICATION
# =========================================================

app.include_router(
    auth_router
)


# =========================================================
# STUDENT PROFILE
# =========================================================

app.include_router(
    student_profile.router
)


# =========================================================
# STUDENT DASHBOARD
# =========================================================

app.include_router(
    student_dashboard.router
)


# =========================================================
# EDUCATION
# =========================================================

app.include_router(
    education.router
)


# =========================================================
# EXPERIENCE
# =========================================================

app.include_router(
    experience.router
)


# =========================================================
# EDUCATION VERIFICATION
# =========================================================

app.include_router(
    education_verification.router
)


# =========================================================
# SKILLS
# =========================================================

app.include_router(
    skills.router
)


# =========================================================
# PROJECTS
# =========================================================

app.include_router(
    projects.router
)


# =========================================================
# CERTIFICATES
# =========================================================

app.include_router(
    certificate.router
)


# =========================================================
# ACHIEVEMENTS
# =========================================================

app.include_router(
    achievement.router
)


# =========================================================
# LANGUAGES
# =========================================================

app.include_router(
    language.router
)


# =========================================================
# MENTOR / IT PROFESSIONAL
# =========================================================

app.include_router(
    mentor.router
)


# =========================================================
# MENTOR → STUDENT
# =========================================================

app.include_router(
    mentor_student.router
)


# =========================================================
# PROJECT VERIFICATION
# =========================================================

app.include_router(
    project_verification.router
)


# =========================================================
# EXPERIENCE VERIFICATION
# =========================================================

app.include_router(
    experience_verification.router
)


# =========================================================
# ENDORSEMENTS
# =========================================================

app.include_router(
    endorsement.router
)


# =========================================================
# OPPORTUNITIES / JOB CALLS
# =========================================================

app.include_router(
    opportunity.router
)


# =========================================================
# SHORTLISTED CANDIDATES
# =========================================================

app.include_router(
    shortlisted.router
)

# =========================================================
# NOTIFICATIONS
# =========================================================

app.include_router(
    notifications.router
)

# =========================================================
# PUBLIC PORTFOLIO
# =========================================================
#
# POST /portfolio/publish
# GET  /portfolio/me
# GET  /portfolio/public/{public_slug}
#
# =========================================================

app.include_router(
    portfolio.router
)


# =========================================================
# AI RESUME
# =========================================================

app.include_router(
    ai_resume.router
)

app.include_router(
    hiring_activity.router
)

# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "CareerVault Builder API is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "success",
        "message": "Backend is connected and healthy",
    }