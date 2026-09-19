from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.job_matcher import compute_similarity
from app.services.skill_extractor import extract_skills

router = APIRouter(tags=["jobs"])


class JobPayload(BaseModel):
    job_description: str


@router.post("/job/analyze")
def analyze_job(payload: JobPayload):
    if not payload.job_description or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")
    skills = extract_skills(payload.job_description)
    return {
        "job_description": payload.job_description,
        "skills": skills,
        "keyword_summary": payload.job_description[:300],
        "semantic_anchor": compute_similarity(payload.job_description, payload.job_description),
    }


@router.post("/match")
def match_resume_job(resume_text: str, job_description: str):
    similarity = compute_similarity(resume_text, job_description)
    return {
        "semantic_match": similarity,
        "job_description": job_description,
        "resume_preview": resume_text[:300],
    }
