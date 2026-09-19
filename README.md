# AI Resume Scanner & Job Matcher

A production-style resume analysis application that parses uploaded resumes, extracts structured information, compares skills to a job description, and provides explainable ATS-style scoring without requiring custom model training for each user upload.

## Overview

This project combines:
- FastAPI backend for file upload, parsing, and analysis endpoints
- React + Vite frontend dashboard and upload flow
- Document parsing with PyMuPDF and python-docx
- NLP-based normalization, section detection, and skill extraction
- Transformer embeddings from a pretrained sentence-transformer model
- Explainable compatibility scoring and recommendations

## Why the app does not require per-user training

The main system uses pretrained transformer embeddings for semantic matching. A new resume is processed by:

Pretrained model
  ↓
Text extraction
  ↓
Normalization and section detection
  ↓
Skill extraction and resume parsing
  ↓
Transformer inference
  ↓
Semantic similarity + scoring
  ↓
Recommendations

This is inference, not training. Training happens before deployment when the base model is created. The application accepts unseen resumes at runtime without adding them to a dataset or retraining.

## Tech stack

- Frontend: React, Vite, Tailwind
- Backend: FastAPI, Pydantic, SQLAlchemy
- Database: SQLite for development
- Document parsing: PyMuPDF, python-docx
- NLP: spaCy, regex, skill ontology
- Deep learning: sentence-transformers, transformers, torch

## Run locally

### Backend

```
cd backend
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## API endpoints

- GET /api/health
- POST /api/resume/upload
- POST /api/resume/analyze
- POST /api/job/analyze
- POST /api/match

## Security and privacy

- Validate file types and size limits
- Remove temporary uploaded files after parsing
- Avoid logging sensitive data in full
- Do not expose secrets in frontend code

## Future optional training

Optional fine-tuning may be added later for tasks like resume classification, job-role classifier, or custom NER. This is a separate pipeline and not required for v1.
