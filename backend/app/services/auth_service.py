from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.models.database import SessionLocal
from app.models.user import UserRecord


bearer_scheme = HTTPBearer(auto_error=False)
TOKEN_TTL_SECONDS = 12 * 60 * 60


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(password_hash).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_value, hash_value = stored_hash.split("$", maxsplit=2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_value)
        expected = base64.urlsafe_b64decode(hash_value)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, now: int | None = None) -> str:
    issued = int(time.time()) if now is None else now
    payload = json.dumps({"sub": user_id, "exp": issued + TOKEN_TTL_SECONDS}, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.new(SECRET_KEY.encode(), body, hashlib.sha256).digest()
    return f"{body.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def decode_access_token(token: str, now: int | None = None) -> int:
    try:
        body_value, signature_value = token.split(".", maxsplit=1)
        body = body_value.encode()
        signature = base64.urlsafe_b64decode(signature_value + "=" * (-len(signature_value) % 4))
        expected = hmac.new(SECRET_KEY.encode(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        payload = json.loads(base64.urlsafe_b64decode(body + b"=" * (-len(body) % 4)))
        current = int(time.time()) if now is None else now
        if int(payload["exp"]) <= current:
            raise ValueError("Expired token")
        user_id = int(payload["sub"])
        if user_id <= 0:
            raise ValueError("Invalid user")
        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.", headers={"WWW-Authenticate": "Bearer"}) from exc


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UserRecord:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to continue.", headers={"WWW-Authenticate": "Bearer"})
    user_id = decode_access_token(credentials.credentials)
    with SessionLocal() as db:
        user = db.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.", headers={"WWW-Authenticate": "Bearer"})
        db.expunge(user)
        return user