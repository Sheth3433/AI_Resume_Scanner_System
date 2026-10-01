from __future__ import annotations

import re
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError

from app.models.database import SessionLocal
from app.models.analysis import AnalysisRecord
from app.models.user import UserRecord
from app.services.auth_service import create_access_token, get_current_user, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["authentication"])
_LOGIN_FAILURES: dict[str, list[float]] = {}
_LOGIN_WINDOW_SECONDS = 15 * 60
_MAX_LOGIN_FAILURES = 5


class CredentialsPayload(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


def _response(user: UserRecord) -> dict:
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@router.post("/register")
def register(payload: CredentialsPayload):
    email = str(payload.email).strip().casefold()
    with SessionLocal() as db:
        if db.query(UserRecord).filter(UserRecord.email == email).first():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = UserRecord(email=email, password_hash=hash_password(payload.password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
        db.refresh(user)
        return _response(user)


@router.post("/login")
def login(payload: CredentialsPayload):
    email = str(payload.email).strip().casefold()
    now = time.monotonic()
    recent_failures = [stamp for stamp in _LOGIN_FAILURES.get(email, []) if now - stamp < _LOGIN_WINDOW_SECONDS]
    if len(recent_failures) >= _MAX_LOGIN_FAILURES:
        _LOGIN_FAILURES[email] = recent_failures
        raise HTTPException(status_code=429, detail="Too many unsuccessful attempts. Try again later.")
    with SessionLocal() as db:
        user = db.query(UserRecord).filter(UserRecord.email == email).first()
        if user is None or not verify_password(payload.password, user.password_hash):
            recent_failures.append(now)
            _LOGIN_FAILURES[email] = recent_failures
            if len(_LOGIN_FAILURES) > 10000:
                expired = [key for key, attempts in _LOGIN_FAILURES.items() if not attempts or now - attempts[-1] >= _LOGIN_WINDOW_SECONDS]
                for key in expired[:5000]:
                    _LOGIN_FAILURES.pop(key, None)
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        _LOGIN_FAILURES.pop(email, None)
        return _response(user)


@router.get("/me")
def current_account(user: UserRecord = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@router.delete("/me")
def delete_current_account(user: UserRecord = Depends(get_current_user)):
    with SessionLocal() as db:
        deleted_analysis_count = db.query(AnalysisRecord).filter(AnalysisRecord.owner_user_id == user.id).delete(synchronize_session=False)
        account = db.get(UserRecord, user.id)
        if account is not None:
            db.delete(account)
        db.commit()
    return {"status": "deleted", "deleted_analysis_count": deleted_analysis_count}