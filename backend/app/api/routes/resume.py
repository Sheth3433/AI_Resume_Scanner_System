from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from app.config import AI_API_KEY, AI_MODEL, AI_PROVIDER, MAX_FILE_SIZE, MODEL_NAME, UPLOAD_DIR
from app.models.analysis import AnalysisRecord
from app.models.database import SessionLocal
from app.models.user import UserRecord
from app.services.auth_service import get_current_user
from app.services.document_parser import parse_resume_content, validate_resume_content
from app.services.resume_parser import build_resume_summary
from app.services.resume_improvement import improve_resume_text
from app.services.report_generator import generate_analysis_report

router = APIRouter(tags=["resume"])


class ComparePayload(BaseModel):
    first_analysis_id: int = Field(gt=0)
    second_analysis_id: int = Field(gt=0)


class ImprovementPayload(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...), current_user: UserRecord = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    try:
        suffix = validate_resume_content(file.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored_name = f"{uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR / stored_name
    with save_path.open("xb") as target:
        target.write(file_bytes)

    return {
        "filename": file.filename,
        "size_bytes": len(file_bytes),
        "status": "uploaded",
    }


@router.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(default=None),
    current_user: UserRecord = Depends(get_current_user),
):
    try:
        content = await file.read(MAX_FILE_SIZE + 1)
        text = parse_resume_content(file.filename or "resume", content)
        result = build_resume_summary(text, job_description or "")
        with SessionLocal() as db:
            record = AnalysisRecord(
                owner_user_id=current_user.id,
                filename=Path(file.filename or "resume").name[:255],
                resume_name=result["resume"]["name"],
                email=result["resume"]["email"],
                compatibility_score=result["scores"]["compatibility"],
                ats_score=result["scores"]["ats_compatibility"],
                semantic_match=result["scores"]["semantic_match"],
                skill_match=result["scores"]["skill_match"],
            )
            db.add(record)
            db.flush()
            result["analysis_id"] = record.id
            record.json_output = json.dumps(result, ensure_ascii=False)
            db.commit()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Resume analysis is temporarily unavailable.") from exc


@router.get("/resumes/history")
def list_analysis_history(current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        records = db.query(AnalysisRecord).filter(AnalysisRecord.owner_user_id == current_user.id).order_by(AnalysisRecord.created_at.desc(), AnalysisRecord.id.desc()).all()
        return [
            {
                "analysis_id": record.id,
                "filename": record.filename,
                "resume_name": record.resume_name or "Unknown Candidate",
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "scores": {
                    "compatibility": record.compatibility_score,
                    "ats_compatibility": record.ats_score,
                    "skill_match": record.skill_match,
                },
            }
            for record in records
        ]


@router.delete("/resumes/history")
def clear_analysis_history(current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        deleted_count = db.query(AnalysisRecord).filter(AnalysisRecord.owner_user_id == current_user.id).delete(synchronize_session=False)
        db.commit()
    return {"status": "cleared", "deleted_count": deleted_count}


@router.get("/settings")
def get_settings_status(current_user: UserRecord = Depends(get_current_user)):
    provider = AI_PROVIDER if AI_PROVIDER in {"openai", "gemini"} else None
    return {
        "ai": {
            "provider": provider,
            "configured": bool(provider and AI_API_KEY),
            "model": AI_MODEL if provider == "openai" else (AI_MODEL if AI_MODEL.startswith("gemini-") else "gemini-2.0-flash") if provider == "gemini" else None,
        },
        "semantic_model": MODEL_NAME,
        "history_storage": "SQLite; analysis records are stored until deleted.",
        "uploaded_files": "Files saved by /resume/upload are separate and are not removed by clearing analysis history.",
    }


@router.get("/resume/{analysis_id}")
def get_saved_analysis(analysis_id: int, current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id, AnalysisRecord.owner_user_id == current_user.id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Analysis was not found.")
        return json.loads(record.json_output or "{}")


@router.get("/report/{analysis_id}")
def download_analysis_report(analysis_id: int, current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id, AnalysisRecord.owner_user_id == current_user.id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Analysis was not found.")
        analysis = json.loads(record.json_output or "{}")
        filename = record.filename
    pdf_bytes = generate_analysis_report(analysis, filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume-analysis-{analysis_id}.pdf"'},
    )


@router.delete("/resume/{analysis_id}")
def delete_saved_analysis(analysis_id: int, current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id, AnalysisRecord.owner_user_id == current_user.id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Analysis was not found.")
        db.delete(record)
        db.commit()
    return {"status": "deleted", "analysis_id": analysis_id}


@router.post("/resume/compare")
def compare_saved_analyses(payload: ComparePayload, current_user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        first = db.query(AnalysisRecord).filter(AnalysisRecord.id == payload.first_analysis_id, AnalysisRecord.owner_user_id == current_user.id).first()
        second = db.query(AnalysisRecord).filter(AnalysisRecord.id == payload.second_analysis_id, AnalysisRecord.owner_user_id == current_user.id).first()
        if not first or not second:
            raise HTTPException(status_code=404, detail="One or both analyses were not found.")
        first_result = json.loads(first.json_output or "{}")
        second_result = json.loads(second.json_output or "{}")

    first_scores = first_result.get("scores", {})
    second_scores = second_result.get("scores", {})
    first_skills = set(first_result.get("resume", {}).get("skills", []))
    second_skills = set(second_result.get("resume", {}).get("skills", []))
    first_sections = set(first_result.get("resume", {}).get("sections_detected", []))
    second_sections = set(second_result.get("resume", {}).get("sections_detected", []))
    score_keys = ("compatibility", "ats_compatibility", "skill_match", "keyword_match")
    return {
        "first_analysis_id": first.id,
        "second_analysis_id": second.id,
        "score_changes": {key: second_scores.get(key, 0) - first_scores.get(key, 0) for key in score_keys},
        "new_skills": sorted(second_skills - first_skills),
        "removed_skills": sorted(first_skills - second_skills),
        "new_sections": sorted(second_sections - first_sections),
        "removed_sections": sorted(first_sections - second_sections),
    }


@router.post("/resume/improve-summary")
def improve_summary(payload: ImprovementPayload, current_user: UserRecord = Depends(get_current_user)):
    return improve_resume_text(payload.text, "summary")


@router.post("/resume/improve-bullet")
def improve_bullet(payload: ImprovementPayload, current_user: UserRecord = Depends(get_current_user)):
    return improve_resume_text(payload.text, "bullet point")
