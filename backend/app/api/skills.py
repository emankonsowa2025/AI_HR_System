"""Skill assessment and analysis endpoints."""

from datetime import datetime
from typing import List, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.services.skill_service import (
    save_skills,
    get_user_skills,
    analyze_skills
)
from backend.services.langchain_adapter import analyze_skills_with_ai
from backend.services.auth_service import auth_service, User

router = APIRouter()

class SkillSubmission(BaseModel):
    skills: List[str]

@router.post("/submit", response_model=Dict)
async def submit_skills(
    submission: SkillSubmission,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Submit and analyze user skills."""
    skills = submission.skills
    if not skills:
        return {"status": "error", "message": "skills must be a non-empty list"}

    # Save skills to database
    save_skills(current_user.id, skills)

    # Analyze using OpenAI
    analysis = analyze_skills_with_ai(skills)

    return {"status": "ok", "analysis": analysis}

@router.get("/suggestions", response_model=Dict)
async def get_suggestions(current_user: User = Depends(auth_service.get_current_user)):
    """Get job and interview suggestions based on user's skills."""
    # Get user's stored skills
    skills = get_user_skills(current_user.id)
    if not skills:
        return {
            "suggestions": {
                "titles": [],
                "questions": [],
                "message": "No skills found. Please submit your skills first."
            }
        }

    # Analyze skills
    analysis = analyze_skills(skills)

    return {"suggestions": analysis}

@router.get("/list", response_model=List[str])
async def list_skills(current_user: User = Depends(auth_service.get_current_user)):
    """Get user's stored skills."""
    return get_user_skills(current_user.id)