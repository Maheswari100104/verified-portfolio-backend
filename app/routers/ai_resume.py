from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import ollama


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/ai/resume",
    tags=["AI Resume"],
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class ResumeSummaryRequest(BaseModel):
    personal: dict[str, Any] | None = None

    education: list[Any] = []
    skills: list[Any] = []
    projects: list[Any] = []
    experience: list[Any] = []
    certificates: list[Any] = []
    achievements: list[Any] = []
    languages: list[Any] = []


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class ResumeSummaryResponse(BaseModel):
    summary: str


# =========================================================
# GENERATE RESUME SUMMARY
# =========================================================

@router.post(
    "/generate-summary",
    response_model=ResumeSummaryResponse,
)
def generate_resume_summary(
    data: ResumeSummaryRequest,
):

    # =====================================================
    # PERSONAL INFORMATION
    # =====================================================

    personal = data.personal or {}

    full_name = personal.get(
        "fullName",
        "",
    )

    headline = personal.get(
        "headline",
        "",
    )

    about = personal.get(
        "about",
        "",
    )


    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = f"""
You are a professional resume writer.

Create a concise and professional resume summary
for the student using ONLY the portfolio information
provided below.

IMPORTANT RULES:

1. Do NOT invent companies, job titles, qualifications,
   skills, achievements, projects, or experience.

2. Use ONLY information provided in the portfolio.

3. Do not mention that you are an AI.

4. Do not use first person such as:
   "I", "my", or "me".

5. Write in professional resume language.

6. Keep the summary between 3 and 5 sentences.

7. Focus on the student's education, skills,
   projects, experience, and career strengths.

8. If information is missing, simply leave it out.

STUDENT INFORMATION
-------------------

Name:
{full_name}

Headline:
{headline}

Existing About:
{about}

Education:
{data.education}

Skills:
{data.skills}

Projects:
{data.projects}

Experience:
{data.experience}

Certificates:
{data.certificates}

Achievements:
{data.achievements}

Languages:
{data.languages}

Write ONLY the final resume summary.
Do not add a heading.
Do not explain your answer.
"""


    # =====================================================
    # CALL LOCAL AI
    # =====================================================

    try:

        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        summary = (
            response["message"]["content"]
            .strip()
        )


    except Exception as error:

        print(
            "AI Resume Summary Error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate resume summary.",
        )


    # =====================================================
    # VALIDATE RESPONSE
    # =====================================================

    if not summary:

        raise HTTPException(
            status_code=500,
            detail="AI returned an empty resume summary.",
        )


    # =====================================================
    # RETURN RESPONSE
    # =====================================================

    return ResumeSummaryResponse(
        summary=summary,
    )