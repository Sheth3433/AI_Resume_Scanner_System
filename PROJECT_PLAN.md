# AI Resume Scanner & Job Matcher - Project Plan

## Phase 1: Project inspection and architecture
- Confirm empty workspace and establish repository structure.
- Define monorepo layout with backend, frontend, docs, data, and tests.
- Document architecture choices around FastAPI, React/Vite, SQLite, spaCy, and Transformers.

## Phase 2: Frontend foundation
- Initialize Vite React app with Tailwind.
- Build responsive app shell, routing, and landing/upload UI.
- Add API client and result dashboard scaffold.

## Phase 3: Backend foundation
- Create FastAPI app with config and environment management.
- Define Pydantic schemas, database models, and app startup lifecycle.
- Add health endpoint and basic error handling.

## Phase 4: File upload
- Implement secure resume upload endpoints.
- Validate file extension, MIME type, size, and empty content.
- Save temporary files safely and clean them up.

## Phase 5: PDF/DOCX extraction
- Support PDF and DOCX text extraction with DOC fallback when available.
- Handle OCR-ready detection for scanned PDFs.
- Normalize extracted text and return clean raw text.

## Phase 6: NLP cleaning and section detection
- Preprocess resume text without destructive stopword removal.
- Detect heading blocks and normalize sections to standard categories.
- Prepare structured text for extraction.

## Phase 7: Structured resume parsing
- Extract contact, education, experience, skills, projects, and certifications.
- Build explainable internal JSON representation of the resume.

## Phase 8: Skill extraction
- Maintain skill taxonomy and aliases.
- Extract category-based skills with evidence and confidence.
- Normalize alias variants like ReactJS -> React.

## Phase 9: Transformer embedding service
- Load pretrained sentence-transformer model once at startup.
- Generate embeddings for resume chunks and job description.
- Support CPU/GPU-safe inference and document the pipeline.

## Phase 10: Job Description analysis
- Parse skills, requirements, responsibilities, and education constraints from JD.
- Build structured job representation for matching.

## Phase 11: Semantic matching
- Combine semantic similarity, skill coverage, and keyword overlap.
- Compute explainable match scores across standard dimensions.

## Phase 12: Explainable scoring
- Build ATS-style compatibility scoring.
- Add reasons, missing skills, and confidence explanations.

## Phase 13: Recommendations
- Generate evidence-based recommendations from actual analysis.
- Avoid generic advice and ensure each suggestion references a resume or job finding.

## Phase 14: Dashboard
- Build a professional results dashboard with score cards, charts, and sections.
- Show resume details, job requirements, missing skills, and issues.

## Phase 15: Database persistence
- Add SQLite models for resumes, analyses, and candidate data.
- Save analysis records and support retrieval by ID.

## Phase 16: Security
- Enforce safe file handling, environment secrets, privacy-safe logging, and cleanup.
- Document limitations and deployment safeguards.

## Phase 17: Testing
- Add unit and API tests for file parsing, extraction, matching, and scoring.
- Validate error handling and security constraints.

## Phase 18: Documentation
- Write project, architecture, API, NLP, deep learning, and scoring docs.
- Explain why pretrained models are used and how training vs inference differs.

## Phase 19: Deployment
- Prepare Docker and production-ready configuration.
- Document backend/frontend commands and model memory requirements.

## Core principles
- Main production flow must work without custom retraining.
- Use pretrained transformer models for inference on unseen resumes.
- Keep a separate optional training pipeline for future fine-tuning, not required in v1.
- All scoring must be explainable and based on actual data.
