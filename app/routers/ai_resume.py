
from typing import Any
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from groq import Groq


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

    education: list[Any] = Field(default_factory=list)
    skills: list[Any] = Field(default_factory=list)
    projects: list[Any] = Field(default_factory=list)
    experience: list[Any] = Field(default_factory=list)
    certificates: list[Any] = Field(default_factory=list)
    achievements: list[Any] = Field(default_factory=list)
    languages: list[Any] = Field(default_factory=list)


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

    full_name = personal.get("fullName", "")
    headline = personal.get("headline", "")
    about = personal.get("about", "")

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
    # CONNECT TO GROQ AI
    # =====================================================

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("AI Resume Summary Error: GROQ_API_KEY is not configured.")

        raise HTTPException(
            status_code=500,
            detail="AI service is not configured.",
        )

    # =====================================================
    # GENERATE SUMMARY USING GROQ
    # =====================================================

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,
            max_completion_tokens=300,
        )

        summary = (
            response.choices[0].message.content or ""
        ).strip()

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
