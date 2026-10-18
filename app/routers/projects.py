from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)

from app.core.dependencies import get_current_user


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# =========================================================
# Helper
# =========================================================

def get_student_profile(
    current_user: User,
    db: Session,
) -> StudentProfile:

    # -----------------------------------------------------
    # Student-only
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can manage projects",
        )

    # -----------------------------------------------------
    # Find logged-in student's profile
    # -----------------------------------------------------

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
            detail="Student profile not found",
        )

    return profile


# =========================================================
# GET MY PROJECTS
# =========================================================
#
# GET /projects/me
#
# Returns all projects belonging to the logged-in student.
#
# =========================================================

@router.get(
    "/me",
    response_model=list[ProjectResponse],
)
def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    projects = (
        db.query(Project)
        .filter(
            Project.student_profile_id == profile.id
        )
        .order_by(Project.id)
        .all()
    )

    return projects


# =========================================================
# GET SINGLE PROJECT
# =========================================================
#
# GET /projects/{project_id}
#
# Only the owner can access the project.
#
# =========================================================

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.student_profile_id == profile.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


# =========================================================
# CREATE PROJECT
# =========================================================
#
# POST /projects
#
# =========================================================

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Ownership check
    # -----------------------------------------------------

    if data.student_profile_id != profile.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You cannot create a project "
                "for another student"
            ),
        )

    # -----------------------------------------------------
    # Clean title
    # -----------------------------------------------------

    title = data.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Project title is required",
        )

    # -----------------------------------------------------
    # Clean description
    # -----------------------------------------------------

    description = data.description.strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="Project description is required",
        )

    # -----------------------------------------------------
    # Validate dates
    # -----------------------------------------------------

    if (
        data.start_date
        and data.end_date
        and data.end_date < data.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    # -----------------------------------------------------
    # Technologies
    # -----------------------------------------------------

    technologies = None

    if data.technologies:

        technologies = data.technologies.strip()

        if not technologies:
            technologies = None

    # -----------------------------------------------------
    # GitHub
    # -----------------------------------------------------

    github = None

    if data.github:

        github = data.github.strip()

        if not github:
            github = None

    # -----------------------------------------------------
    # Live Demo
    # -----------------------------------------------------

    live_demo = None

    if data.live_demo:

        live_demo = data.live_demo.strip()

        if not live_demo:
            live_demo = None

    # -----------------------------------------------------
    # Image
    # -----------------------------------------------------

    image = None

    if data.image:

        image = data.image.strip()

        if not image:
            image = None

    # -----------------------------------------------------
    # Create Project
    # -----------------------------------------------------

    project = Project(
        student_profile_id=profile.id,

        title=title,

        description=description,

        technologies=technologies,

        github=github,

        live_demo=live_demo,

        image=image,

        start_date=data.start_date,

        end_date=data.end_date,

        is_current=data.is_current,
    )

    db.add(project)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(project)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create project",
        )

    return project


# =========================================================
# UPDATE PROJECT
# =========================================================
#
# PUT /projects/{project_id}
#
# =========================================================

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find project belonging to logged-in student
    # -----------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.student_profile_id == profile.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # -----------------------------------------------------
    # Get only fields supplied by frontend
    # -----------------------------------------------------

    update_data = data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    if "title" in update_data:

        title = update_data["title"]

        if title is None:
            raise HTTPException(
                status_code=400,
                detail="Project title cannot be empty",
            )

        title = title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Project title cannot be empty",
            )

        update_data["title"] = title

    # -----------------------------------------------------
    # Description
    # -----------------------------------------------------

    if "description" in update_data:

        description = update_data["description"]

        if description is None:
            raise HTTPException(
                status_code=400,
                detail="Project description cannot be empty",
            )

        description = description.strip()

        if not description:
            raise HTTPException(
                status_code=400,
                detail="Project description cannot be empty",
            )

        update_data["description"] = description

    # -----------------------------------------------------
    # Clean optional text fields
    # -----------------------------------------------------

    for field in [
        "technologies",
        "github",
        "live_demo",
        "image",
    ]:

        if field in update_data:

            value = update_data[field]

            if isinstance(value, str):

                value = value.strip()

                update_data[field] = (
                    value if value else None
                )

    # -----------------------------------------------------
    # Validate dates
    # -----------------------------------------------------

    start_date = update_data.get(
        "start_date",
        project.start_date,
    )

    end_date = update_data.get(
        "end_date",
        project.end_date,
    )

    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    # -----------------------------------------------------
    # Apply updates
    # -----------------------------------------------------

    for field, value in update_data.items():

        setattr(
            project,
            field,
            value,
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(project)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update project",
        )

    return project


# =========================================================
# DELETE PROJECT
# =========================================================
#
# DELETE /projects/{project_id}
#
# =========================================================

@router.delete(
    "/{project_id}"
)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    # -----------------------------------------------------
    # Find project belonging to logged-in student
    # -----------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.student_profile_id == profile.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    db.delete(project)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete project",
        )

    return {
        "message": "Project deleted successfully",
        "project_id": project_id,
    }