import hashlib
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.education import Education
from app.models.education_verification import EducationVerification
from app.services.education_ocr import extract_text_from_image


router = APIRouter(
    prefix="/api/education",
    tags=["Education Verification"],
)


# =========================================================
# Text Normalization
# =========================================================

def normalize_text(value: str | None) -> str:
    """
    Normalize text for OCR comparison.

    Handles:
    - Lowercase conversion
    - Common degree abbreviations
    - Punctuation
    - Extra spaces
    """

    if not value:
        return ""

    value = value.lower().strip()

    replacements = {
        "m.sc.": "master of science",
        "m.sc": "master of science",
        "b.sc.": "bachelor of science",
        "b.sc": "bachelor of science",
        "m.tech.": "master of technology",
        "m.tech": "master of technology",
        "b.tech.": "bachelor of technology",
        "b.tech": "bachelor of technology",
        "m.e.": "master of engineering",
        "m.e": "master of engineering",
        "b.e.": "bachelor of engineering",
        "b.e": "bachelor of engineering",
        "mca": "master of computer applications",
        "bca": "bachelor of computer applications",
        "mba": "master of business administration",
    }

    for short_form, full_form in replacements.items():
        value = value.replace(short_form, full_form)

    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# =========================================================
# Fuzzy Text Matching
# =========================================================

def text_matches(
    document_text: str,
    expected_value: str | None,
    threshold: float = 0.80,
) -> bool:
    """
    Compare expected information with OCR text.

    Missing expected values are NOT counted as matches.
    """

    # Do not count missing database values as matches.
    if not expected_value or not expected_value.strip():
        return False

    document = normalize_text(document_text)
    expected = normalize_text(expected_value)

    if not document or not expected:
        return False

    # Direct match
    if expected in document:
        return True

    # Line-based fuzzy matching
    lines = document.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        similarity = SequenceMatcher(
            None,
            expected,
            line,
        ).ratio()

        if similarity >= threshold:
            return True

    # Word-window fuzzy matching
    words = document.split()
    expected_words = expected.split()
    window_size = len(expected_words)

    if window_size > 0:
        for index in range(len(words) - window_size + 1):
            chunk = " ".join(
                words[index:index + window_size]
            )

            similarity = SequenceMatcher(
                None,
                expected,
                chunk,
            ).ratio()

            if similarity >= threshold:
                return True

    return False


# =========================================================
# Verify Education
# =========================================================

@router.post("/{education_id}/verify")
async def verify_education(
    education_id: int,
    document: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # =====================================================
    # 1. Find Education Record
    # =====================================================

    education = (
        db.query(Education)
        .filter(Education.id == education_id)
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=404,
            detail="Education record not found.",
        )

    # =====================================================
    # 2. Validate File Type
    # =====================================================

    allowed_types = {
        "image/jpeg",
        "image/png",
    }

    if document.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "For now, only JPG and PNG "
                "documents are supported."
            ),
        )

    # =====================================================
    # 3. Read Uploaded File
    # =====================================================

    file_data = await document.read()

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded document is empty.",
        )

    # =====================================================
    # 4. Duplicate Detection
    # =====================================================

    document_hash = hashlib.sha256(
        file_data
    ).hexdigest()

    existing_document = (
        db.query(EducationVerification)
        .filter(
            EducationVerification.document_hash
            == document_hash
        )
        .first()
    )

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail=(
                "This document has already "
                "been submitted."
            ),
        )

    # =====================================================
    # 5. Extract Text Using OCR
    # =====================================================

    try:
        extracted_text = extract_text_from_image(
            file_data
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {error}",
        ) from error

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text was found in the "
                "document. Please upload a clearer image."
            ),
        )

    # =====================================================
    # 6. Compare Education Information
    # =====================================================

    institution_match = text_matches(
        extracted_text,
        education.institution,
    )

    degree_match = text_matches(
        extracted_text,
        education.degree,
    )

    field_match = text_matches(
        extracted_text,
        education.field_of_study,
    )

    start_year_match = text_matches(
        extracted_text,
        str(education.start_date)
        if education.start_date is not None
        else None,
    )

    end_year_match = text_matches(
        extracted_text,
        str(education.end_date)
        if education.end_date is not None
        else None,
    )

    # =====================================================
    # 7. Calculate Matching Score
    # =====================================================

    checks = {
        "institution": institution_match,
        "degree": degree_match,
        "field_of_study": field_match,
        "start_year": start_year_match,
        "end_year": end_year_match,
    }

    matched_fields = sum(
        1 for matched in checks.values()
        if matched
    )

    total_fields = len(checks)

    # Core fields provide stronger evidence.
    core_match = institution_match or degree_match

    # =====================================================
    # 8. Determine Verification Status
    # =====================================================

    if matched_fields >= 3 and core_match:
        status = "MATCHED"

        message = (
            f"Education details matched successfully: "
            f"{matched_fields} out of {total_fields} "
            f"fields matched."
        )

    elif matched_fields >= 2 and core_match:
        status = "MISMATCH"

        message = (
            f"Partial match: {matched_fields} out of "
            f"{total_fields} fields matched. "
            f"Additional verification is required."
        )

    else:
        status = "FLAGGED"

        message = (
            f"Insufficient matching information: "
            f"{matched_fields} out of {total_fields} "
            f"fields matched. Please review your "
            f"registered details or upload a clearer document."
        )

    # =====================================================
    # 9. Save Verification Result
    # =====================================================

       # =====================================================
    # 9. Save or Update Verification Result
    # =====================================================

    verification = (
        db.query(EducationVerification)
        .filter(
            EducationVerification.education_id == education_id
        )
        .first()
    )

    if verification is None:
        verification = EducationVerification(
            education_id=education_id,
        )
        db.add(verification)

    verification.document = file_data
    verification.document_name = (
        document.filename or "education_document"
    )
    verification.document_type = (
        document.content_type or "application/octet-stream"
    )
    verification.document_size = len(file_data)
    verification.document_hash = document_hash
    verification.ocr_data = extracted_text
    verification.status = status
    verification.verification_message = message
    verification.checked_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(verification)
    except Exception:
        db.rollback()
        raise
    # =====================================================
    # 10. Return Verification Result
    # =====================================================

    return {
        "message": message,
        "education_id": education_id,
        "verification_id": verification.id,
        "status": status,
        "checks": checks,
        "matched_fields": matched_fields,
        "total_fields": total_fields,
    }


# =========================================================
# Get Education Verification Status
# =========================================================

@router.get("/{education_id}/verification")
def get_education_verification(
    education_id: int,
    db: Session = Depends(get_db),
):
    # =====================================================
    # 1. Find Education Record
    # =====================================================

    education = (
        db.query(Education)
        .filter(Education.id == education_id)
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=404,
            detail="Education record not found.",
        )

    # =====================================================
    # 2. Find Latest Verification
    # =====================================================

    verification = (
        db.query(EducationVerification)
        .filter(
            EducationVerification.education_id
            == education_id
        )
        .order_by(
            EducationVerification.checked_at.desc()
        )
        .first()
    )

    # =====================================================
    # 3. No Document Submitted
    # =====================================================

    if not verification:
        return {
            "education_id": education_id,
            "status": "NOT_SUBMITTED",
            "message": (
                "Education document has not been submitted."
            ),
        }

    # =====================================================
    # 4. Return Verification Status
    # =====================================================

    return {
        "education_id": education_id,
        "verification_id": verification.id,
        "status": verification.status,
        "message": verification.verification_message,
        "document_name": verification.document_name,
        "checked_at": verification.checked_at,
    }