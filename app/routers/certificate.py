from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.certificate import Certificate
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
    CertificateUpdate,
)


router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
)


# ============================================================
# STUDENT PROFILE HELPER
# ============================================================

def get_student_profile(
    current_user: User,
    db: Session,
) -> StudentProfile:

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access certificates",
        )

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


# ============================================================
# BUILD CERTIFICATE RESPONSE
# ============================================================

def build_certificate_response(
    certificate: Certificate,
) -> CertificateResponse:

    response = CertificateResponse.model_validate(
        certificate
    )

    if certificate.certificate_file:
        response.certificate_file_url = (
            f"/certificates/{certificate.id}/file"
        )
    else:
        response.certificate_file_url = None

    return response


# ============================================================
# GET MY CERTIFICATES
# ============================================================

@router.get(
    "/me",
    response_model=list[CertificateResponse],
)
def get_my_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificates = (
        db.query(Certificate)
        .filter(
            Certificate.student_profile_id == profile.id
        )
        .order_by(
            Certificate.id.desc()
        )
        .all()
    )

    return [
        build_certificate_response(certificate)
        for certificate in certificates
    ]


# ============================================================
# GET SINGLE CERTIFICATE
# ============================================================

@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
)
def get_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return build_certificate_response(
        certificate
    )


# ============================================================
# CREATE CERTIFICATE
# ============================================================

@router.post(
    "",
    response_model=CertificateResponse,
)
def create_certificate(
    certificate_data: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )


    certificate_data_dict = certificate_data.model_dump(
        exclude={"student_profile_id"}
    )

    certificate = Certificate(
        student_profile_id=profile.id,
        **certificate_data_dict,
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return build_certificate_response(
        certificate
    )


# ============================================================
# UPDATE CERTIFICATE
# ============================================================

@router.put(
    "/{certificate_id}",
    response_model=CertificateResponse,
)
def update_certificate(
    certificate_id: int,
    certificate_data: CertificateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    update_data = certificate_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            certificate,
            field,
            value,
        )

    db.commit()
    db.refresh(certificate)

    return build_certificate_response(
        certificate
    )


# ============================================================
# DELETE CERTIFICATE
# ============================================================

@router.delete(
    "/{certificate_id}"
)
def delete_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    db.delete(certificate)
    db.commit()

    return {
        "message": "Certificate deleted successfully"
    }


# ============================================================
# UPLOAD CERTIFICATE PDF
# ============================================================

@router.post(
    "/{certificate_id}/file"
)
async def upload_certificate_file(
    certificate_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    file_data = await file.read()

    # --------------------------------------------------------
    # Validate file size
    # Maximum = 10 MB
    # --------------------------------------------------------

    max_size = 10 * 1024 * 1024

    if len(file_data) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Certificate file size must be less than 10 MB",
        )

    if len(file_data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded certificate file is empty",
        )

    # --------------------------------------------------------
    # Store file
    # --------------------------------------------------------

    certificate.certificate_file = file_data
    certificate.certificate_file_name = (
        file.filename
    )
    certificate.certificate_file_type = (
        file.content_type
    )
    certificate.certificate_file_size = (
        len(file_data)
    )

    db.commit()
    db.refresh(certificate)

    return {
        "message": "Certificate PDF uploaded successfully",
        "certificate_id": certificate.id,
        "file_name": certificate.certificate_file_name,
        "file_type": certificate.certificate_file_type,
        "file_size": certificate.certificate_file_size,

        # Authenticated URL
        "certificate_file_url": (
            f"/certificates/{certificate.id}/file"
        ),

        # Public URL
        "public_certificate_file_url": (
            f"/certificates/public/{certificate.id}/file"
        ),
    }


# ============================================================
# PUBLIC CERTIFICATE PDF
# ============================================================
#
# IMPORTANT:
# This route MUST appear BEFORE:
#
#     /{certificate_id}/file
#
# Otherwise "public" can be interpreted as certificate_id.
#
# This endpoint does NOT require login.
# It is used by the public portfolio.
# ============================================================

@router.get(
    "/public/{certificate_id}/file"
)
def get_public_certificate_file(
    certificate_id: int,
    db: Session = Depends(get_db),
):

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if not certificate.certificate_file:
        raise HTTPException(
            status_code=404,
            detail="Certificate PDF not found",
        )

    return Response(
        content=certificate.certificate_file,
        media_type=(
            certificate.certificate_file_type
            or "application/pdf"
        ),
        headers={
            "Content-Disposition": (
                'inline; filename="'
                f'{certificate.certificate_file_name or "certificate.pdf"}'
                '"'
            ),
            "Cache-Control": "public, max-age=3600",
        },
    )


# ============================================================
# GET CERTIFICATE PDF - AUTHENTICATED
# ============================================================

@router.get(
    "/{certificate_id}/file"
)
def get_certificate_file(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if not certificate.certificate_file:
        raise HTTPException(
            status_code=404,
            detail="Certificate PDF not found",
        )

    return Response(
        content=certificate.certificate_file,
        media_type=(
            certificate.certificate_file_type
            or "application/pdf"
        ),
        headers={
            "Content-Disposition": (
                'inline; filename="'
                f'{certificate.certificate_file_name or "certificate.pdf"}'
                '"'
            ),
            "Cache-Control": "no-cache",
        },
    )


# ============================================================
# DELETE CERTIFICATE PDF
# ============================================================

@router.delete(
    "/{certificate_id}/file"
)
def delete_certificate_file(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile = get_student_profile(
        current_user,
        db,
    )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_profile_id == profile.id,
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if not certificate.certificate_file:
        raise HTTPException(
            status_code=404,
            detail="Certificate PDF not found",
        )

    # --------------------------------------------------------
    # Remove file data
    # --------------------------------------------------------

    certificate.certificate_file = None
    certificate.certificate_file_name = None
    certificate.certificate_file_type = None
    certificate.certificate_file_size = None

    db.commit()

    return {
        "message": "Certificate PDF deleted successfully"
    }