from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_scanner.db")
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng").strip() or "eng"
OCR_MAX_PAGES = max(1, int(os.getenv("OCR_MAX_PAGES", "20")))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "tmp" / "uploads"))
if not UPLOAD_DIR.is_absolute():
	UPLOAD_DIR = BASE_DIR / UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
APP_ENV = os.getenv("APP_ENV", "development")
if APP_ENV.casefold() == "production" and (SECRET_KEY == "development-secret-key" or len(SECRET_KEY) < 32):
	raise RuntimeError("Production requires a SECRET_KEY with at least 32 characters.")
AI_PROVIDER = os.getenv("AI_PROVIDER", "").strip().lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
