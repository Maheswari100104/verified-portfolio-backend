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

def normalize_text(
    value: str | None,
) -> str:
    """
    Normalize text for OCR comparison.

    Handles:
    - lowercase conversion
    - common degree abbreviations
    - punctuation
    - extra spaces
    """

    if not value:
        return ""

    value = value.lower().strip()

    # -----------------------------------------------------
    # Common academic abbreviations
    # -----------------------------------------------------

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
        value = value.replace(
            short_form,
            full_form
        )

    # -----------------------------------------------------
    # Remove punctuation
    # -----------------------------------------------------

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )

    # -----------------------------------------------------
    # Remove extra spaces
    # -----------------------------------------------------

    value = re.sub(
        r"\s+",
        " ",
        value
    )

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
    Check whether expected information exists
    in OCR text using direct and fuzzy matching.
    """

    if not expected_value:
        return True

    document = normalize_text(
        document_text
    )

    expected = normalize_text(
        expected_value
    )

    if not document or not expected:
        return False

    # -----------------------------------------------------
    # Direct match
    # -----------------------------------------------------

    if expected in document:
        return True

    # -----------------------------------------------------
    # Line-based fuzzy matching
    # -----------------------------------------------------

    lines = document.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        similarity = SequenceMatcher(
            None,
            expected,
            line
        ).ratio()

        if similarity >= threshold:
            return True

    # -----------------------------------------------------
    # Word-window fuzzy matching
    # -----------------------------------------------------

    words = document.split()

    expected_words = expected.split()

    window_size = len(
        expected_words
    )

    if window_size > 0:

        for index in range(
            len(words) - window_size + 1
        ):

            chunk = " ".join(
                words[
                    index:index + window_size
                ]
            )

            similarity = SequenceMatcher(
                None,
                expected,
                chunk
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
    # 1. Find Education
    # =====================================================

    education = (
        db.query(Education)
        .filter(
            Education.id == education_id
        )
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=404,
            detail="Education record not found",
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
    # 3. Read File
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
    # 5. OCR
    # =====================================================

    try:

        extracted_text = (
            extract_text_from_image(
                file_data
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"OCR processing failed: {error}"
            ),
        )

    if not extracted_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text was found "
                "in the document."
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
        education.start_date,
    )

    end_year_match = text_matches(
        extracted_text,
        education.end_date,
    )

    # =====================================================
    # 7. Separate Core & Supporting Checks
    # =====================================================

    core_checks = [
        institution_match,
        degree_match,
    ]

    supporting_checks = [
        field_match,
        start_year_match,
        end_year_match,
    ]

    core_matched = sum(
        core_checks
    )

    supporting_matched = sum(
        supporting_checks
    )

    # =====================================================
    # 8. Determine Verification Status
    # =====================================================

    if (
        core_matched == 2
        and supporting_matched >= 1
    ):

        status = "MATCHED"

        message = (
            "Education information matched "
            "the submitted document."
        )

    elif core_matched >= 1:

        status = "MISMATCH"

        message = (
            "Some education information matched, "
            "but additional details could not "
            "be confirmed."
        )

    else:

        status = "FLAGGED"

        message = (
            "The submitted document could not "
            "be matched sufficiently with the "
            "education record."
        )

    # =====================================================
    # 9. Store Verification
    # =====================================================

    verification = EducationVerification(
        education_id=education_id,

        document=file_data,

        document_name=(
            document.filename
            or "education_document"
        ),

        document_type=(
            document.content_type
            or "application/octet-stream"
        ),

        document_size=len(file_data),

        document_hash=document_hash,

        ocr_data=extracted_text,

        status=status,

        verification_message=message,

        checked_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(
        verification
    )

    db.commit()

    db.refresh(
        verification
    )

    # =====================================================
    # 10. Return Verification Result
    # =====================================================

    return {
        "message": message,

        "education_id": education_id,

        "verification_id": verification.id,

        "status": status,

        "checks": {
            "institution": institution_match,
            "degree": degree_match,
            "field_of_study": field_match,
            "start_year": start_year_match,
            "end_year": end_year_match,
        },

        "matched_fields": (
            core_matched
            + supporting_matched
        ),

        "total_fields": 5,
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
    # 1. Check Education
    # =====================================================

    education = (
        db.query(Education)
        .filter(
            Education.id == education_id
        )
        .first()
    )

    if not education:
        raise HTTPException(
            status_code=404,
            detail="Education record not found.",
        )

    # =====================================================
    # 2. Find Verification
    # =====================================================

    verification = (
        db.query(EducationVerification)
        .filter(
            EducationVerification.education_id
            == education_id
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
                "Education document has not "
                "been submitted."
            ),
        }

    # =====================================================
    # 4. Return Verification Status
    # =====================================================

    return {
        "education_id": education_id,

        "verification_id": verification.id,

        "status": verification.status,

        "message": (
            verification.verification_message
        ),

        "document_name": (
            verification.document_name
        ),

        "checked_at": (
            verification.checked_at
        ),
    }