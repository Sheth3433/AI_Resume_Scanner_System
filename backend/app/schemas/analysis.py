from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeSummary(BaseModel):
    name: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    skills: list[str] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    certifications: list[dict] = Field(default_factory=list)


class JobSummary(BaseModel):
    skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)


class ScoreSummary(BaseModel):
    compatibility: float = 0.0
    semantic_match: float = 0.0
    skill_match: float = 0.0
    keyword_match: float = 0.0
    experience_match: float = 0.0
    education_match: float = 0.0


class AnalysisResult(BaseModel):
    resume: ResumeSummary
    job: JobSummary
    scores: ScoreSummary
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
