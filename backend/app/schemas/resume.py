from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    filename: str
    saved_path: str
    size_bytes: int
    status: str


class ResumeAnalysisRequest(BaseModel):
    job_description: str | None = None
