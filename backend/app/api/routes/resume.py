from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import MAX_FILE_SIZE, UPLOAD_DIR
from app.services.document_parser import parse_resume_content
from app.services.resume_parser import build_resume_summary

router = APIRouter(tags=["resume"])


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    ext = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".doc", ".docx"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Please upload a PDF or DOCX resume.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds the maximum allowed size.")

    safe_name = Path(file.filename).name.replace("..", "").replace("/", "").replace("\\", "")
    save_path = UPLOAD_DIR / safe_name
    with open(save_path, "wb") as target:
        target.write(file_bytes)

    return {
        "filename": file.filename,
        "saved_path": str(save_path),
        "size_bytes": len(file_bytes),
        "status": "uploaded",
    }


@router.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(default=None),
):
    try:
        content = await file.read()
        text = parse_resume_content(file.filename or "resume", content)
        result = build_resume_summary(text, job_description or "")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Resume analysis is temporarily unavailable.") from exc
