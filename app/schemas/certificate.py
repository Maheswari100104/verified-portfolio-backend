from datetime import date
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
)


# =========================================================
# Create Certificate
# =========================================================

class CertificateCreate(BaseModel):

    student_profile_id: int

    title: str

    issuer: str

    issue_date: Optional[date] = None

    expiry_date: Optional[date] = None

    credential_id: Optional[str] = None

    credential_url: Optional[str] = None

    description: Optional[str] = None

    image: Optional[str] = None


# =========================================================
# Update Certificate
# =========================================================

class CertificateUpdate(BaseModel):

    title: Optional[str] = None

    issuer: Optional[str] = None

    issue_date: Optional[date] = None

    expiry_date: Optional[date] = None

    credential_id: Optional[str] = None

    credential_url: Optional[str] = None

    description: Optional[str] = None

    image: Optional[str] = None


# =========================================================
# Certificate Response
# =========================================================

class CertificateResponse(BaseModel):

    id: int

    student_profile_id: int

    title: str

    issuer: str

    issue_date: Optional[date] = None

    expiry_date: Optional[date] = None

    credential_id: Optional[str] = None

    credential_url: Optional[str] = None

    description: Optional[str] = None

    image: Optional[str] = None

    # =====================================================
    # PDF Information
    # =====================================================

    certificate_file_name: Optional[str] = None

    certificate_file_type: Optional[str] = None

    certificate_file_size: Optional[int] = None

    certificate_file_url: Optional[str] = None

    # =====================================================
    # Pydantic Configuration
    # =====================================================

    model_config = ConfigDict(
        from_attributes=True
    )