from pydantic import BaseModel
from typing import Any, Optional


class PortfolioCreate(BaseModel):
    user_id: int
    title: Optional[str] = "My Portfolio"
    template: Optional[str] = "minimal"

    personal: Optional[Any] = None
    education: Optional[Any] = None
    skills: Optional[Any] = None
    projects: Optional[Any] = None
    experience: Optional[Any] = None
    certificates: Optional[Any] = None
    achievements: Optional[Any] = None
    languages: Optional[Any] = None


class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    template: Optional[str] = None

    personal: Optional[Any] = None
    education: Optional[Any] = None
    skills: Optional[Any] = None
    projects: Optional[Any] = None
    experience: Optional[Any] = None
    certificates: Optional[Any] = None
    achievements: Optional[Any] = None
    languages: Optional[Any] = None

    is_published: bool

    class Config:
        from_attributes = True