from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.job_matcher import compute_semantic_similarity, compute_similarity
from app.services.skill_extractor import extract_skills
from app.services.role_profiles import list_role_profiles
from app.models.user import UserRecord
from app.services.auth_service import get_current_user

router = APIRouter(tags=["jobs"])


@router.get("/roles")
def get_supported_roles(current_user: UserRecord = Depends(get_current_user)):
    return list_role_profiles()


class JobPayload(BaseModel):
    job_description: str


@router.post("/job/analyze")
def analyze_job(payload: JobPayload, current_user: UserRecord = Depends(get_current_user)):
    if not payload.job_description or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")
    skills = extract_skills(payload.job_description)
    return {
        "job_description": payload.job_description,
        "skills": skills,
        "keyword_summary": payload.job_description[:300],
    }


@router.post("/match")
def match_resume_job(resume_text: str, job_description: str, current_user: UserRecord = Depends(get_current_user)):
    similarity, source = compute_semantic_similarity(resume_text, job_description)
    return {
        "semantic_match": similarity,
        "semantic_match_source": source,
        "keyword_match": compute_similarity(resume_text, job_description),
        "job_description": job_description,
        "resume_preview": resume_text[:300],
    }
