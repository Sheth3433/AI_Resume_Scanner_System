# AI Resume Scanner & Job Matcher

A local-first resume analysis application built with React, Vite, FastAPI, and Python. Upload a text-based PDF or DOCX, optionally add a job description, and review extracted resume details, an estimated ATS compatibility score, semantic and keyword comparisons, skill gaps, recommendations, saved analyses, version comparisons, and optional resume wording improvements.

> **Status:** The current app is a working analysis prototype, not a complete hiring or HR platform. It uses sentence-transformer embeddings when available, account-scoped SQLite analysis history, downloadable PDF reports, evidence-backed skill gaps, role suggestions, and privacy settings. OCR and complete structured career-history extraction are not available. Scores are estimates, not hiring decisions.

## Contents

- [Features](#features)
- [Application flow](#application-flow)
- [Architecture](#architecture)
- [Analysis and scoring](#analysis-and-scoring)
- [Run locally on Windows](#run-locally-on-windows)
- [Configuration](#configuration)
- [API](#api)
- [Data, privacy, and security](#data-privacy-and-security)
- [Tests and checks](#tests-and-checks)
- [Known limitations](#known-limitations)

## Features

### Scanner UI

- Single-page, responsive scanner with Analyze, Results, History, Improve, and Settings navigation.
- Email/password registration and sign-in, 12-hour signed bearer sessions, sign-out, and account-isolated analysis history.
- Five failed sign-ins per account within a 15-minute window are throttled by the current API process.
- Drag-and-drop and keyboard-accessible file picker for PDF and DOCX only.
- Client-side extension, empty-file, and 10 MiB size checks; the backend repeats validation and checks document signatures/structure.
- Selected filename and size preview, remove/replace action, optional job-description field, progress status, API error messages, and empty states.
- Results for overall job compatibility, estimated ATS compatibility, skill match, and text similarity.
- Matched skills, skills not detected in the resume, extracted contact/section details, findings, and recommendations.
- ATS checks include supporting evidence and clearly mark document layout as unassessed.
- History supports open, delete, clear-all, PDF download, and compare-two-analyses workflows, with score changes and added/removed skills and sections.
- Downloadable PDF analysis report with candidate details, scores, skills, ATS checks, recommendations, and heuristic limitations.
- Role suggestions based on exact skill overlap with explainable matched/missing role signals; sparse resumes do not get arbitrary suggestions.
- Settings/Privacy screen shows non-secret provider status, storage/retention notes, and clear-history action.
- Summary and bullet wording suggestions. Provider output is identified as AI-assisted; the local fallback is identified as rule-based.
- Neutral responsive layout, visible keyboard focus, and reduced-motion support.

### Backend analysis

- FastAPI API with health, upload, analysis, job-analysis, matching, history, comparison, and wording-improvement endpoints.
- PyMuPDF PDF extraction and `python-docx` DOCX paragraph extraction, whitespace cleanup, and safe unique temporary analysis files.
- PDF signature and DOCX archive/document validation, supported-extension and size checks, and clean errors for unreadable, empty, protected, or textless files.
- Heading-based section detection; regular-expression contact detection; alias-aware skills from the maintained in-code taxonomy.
- Skill records contain source line, detected section, and section-weighted confidence; common aliases are canonicalized and explicit negative mentions are ignored.
- Job skills are classified as required, preferred, or mentioned from nearby wording; required skills count more than preferred/unspecified skills in the skill-match subscore.
- Cached sentence-transformer model (`MODEL_NAME`, default `sentence-transformers/all-MiniLM-L6-v2`) for semantic similarity. If model loading/inference fails, token cosine similarity is used and the response names the fallback source.
- Deterministic hybrid job score and explainable estimated ATS checks.
- SQLite storage for analysis result records, plus list/get/delete/clear/compare operations. Raw uploaded document bytes are not saved by the analysis endpoint.
- Salted scrypt password hashes, HMAC-SHA256 signed tokens, authenticated application routes, and owner-filtered analysis records.
- Optional server-side OpenAI or Gemini wording improvement. No provider key is sent to the browser. Provider errors fall back to a labeled rule-based rewrite.

## Application flow

```text
React scanner
  -> POST /api/resume/analyze (multipart PDF/DOCX + optional job description)
  -> extension, size, signature and document checks
  -> unique temporary file -> PDF/DOCX text extraction -> cleanup
  -> text normalization -> section/contact/skill extraction
  -> cached transformer similarity (or named token-overlap fallback)
  -> hybrid match score + ATS checks + recommendations
  -> persist analysis result in SQLite -> render results
```

The standalone upload endpoint stores a file under a generated UUID name in `UPLOAD_DIR`; the scanner UI uses the analysis endpoint, which removes its temporary file after parsing.

## Architecture

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/routes/       # Health, resume, job and matching endpoints
|   |   |-- models/           # SQLAlchemy analysis model and engine/session
|   |   |-- schemas/          # Pydantic schemas
|   |   |-- services/         # Parsing, semantic matching, ATS and improvement
|   |   |-- config.py         # Environment-backed settings
|   |   `-- main.py           # FastAPI app, CORS, router and DB initialization
|   |-- tests/                # Service, scoring, fallback and persistence tests
|   |-- .env.example
|   `-- requirements.txt
|-- frontend/
|   |-- src/App.jsx           # Scanner, results, history, compare and improvements UI
|   |-- src/App.css           # Responsive application styles
|   |-- src/index.css         # Global tokens and base styles
|   |-- .env.example
|   `-- package.json
|-- docs/                     # Supporting design and pipeline notes
|-- data/skills/              # Skill data area (runtime taxonomy currently lives in code)
|-- tmp/uploads/              # Explicit upload endpoint destination
`-- README.md
```

### Important implementation modules

| Path | Responsibility |
| --- | --- |
| [frontend/src/App.jsx](frontend/src/App.jsx) | Upload/validation UI, API calls, result rendering, saved history, comparison, wording improvement. |
| [frontend/src/App.css](frontend/src/App.css) | Neutral visual system, responsive layouts, states, and component styling. |
| [backend/app/main.py](backend/app/main.py) | FastAPI lifecycle, SQLite table creation, configured CORS, and router registration. |
| [backend/app/api/routes/resume.py](backend/app/api/routes/resume.py) | Upload/analyze, analysis persistence, history, comparison, PDF report, and improvement endpoints. |
| [backend/app/api/routes/jobs.py](backend/app/api/routes/jobs.py) | Job skill extraction and semantic/keyword matching endpoints. |
| [backend/app/api/routes/auth.py](backend/app/api/routes/auth.py) | Account registration, login, and current-account endpoint. |
| [backend/app/services/auth_service.py](backend/app/services/auth_service.py) | Password hashing, signed sessions, and bearer account lookup. |
| [backend/app/services/document_parser.py](backend/app/services/document_parser.py) | Document signature checks, PDF/DOCX extraction, cleanup, and parser error normalization. |
| [backend/app/services/resume_parser.py](backend/app/services/resume_parser.py) | Analysis orchestration, extraction, weighted match score, and response construction. |
| [backend/app/services/job_matcher.py](backend/app/services/job_matcher.py) | Full-vocabulary token cosine and transformer semantic similarity with fallback. |
| [backend/app/services/embedding_service.py](backend/app/services/embedding_service.py) | Lazy, process-cached sentence-transformer loading and encoding. |
| [backend/app/services/ats_scorer.py](backend/app/services/ats_scorer.py) | Deterministic estimated ATS checks, score, and evidence. |
| [backend/app/services/recommendation_engine.py](backend/app/services/recommendation_engine.py) | Prioritized action plan linked to detected gaps, sections, and resume evidence. |
| [backend/app/services/role_recommender.py](backend/app/services/role_recommender.py) | Exact-overlap, explainable role suggestions from extracted skills. |
| [backend/app/services/resume_improvement.py](backend/app/services/resume_improvement.py) | Optional OpenAI/Gemini calls and clearly labeled local fallback. |
| [backend/app/services/report_generator.py](backend/app/services/report_generator.py) | Creates a printable PDF analysis report from saved result data. |
| [backend/app/models/analysis.py](backend/app/models/analysis.py) | Persistent analysis metadata and JSON result. |

## Analysis and scoring

### Job compatibility

When a job description is provided, `scores.compatibility` is a deterministic weighted sum:

| Component | Weight | Current measurement |
| --- | ---: | --- |
| Semantic similarity | 30% | Cosine similarity between normalized sentence-transformer embeddings. |
| Skills | 30% | Weighted coverage of detected job skills: required = 2, mentioned = 1, preferred = 0.5. |
| Keywords | 15% | Token-count cosine similarity over the union of resume and job tokens. |
| Experience | 10% | 100 if an experience section contains text, otherwise 0. Relevance is not assessed. |
| Projects | 10% | 100 if a projects section contains text, otherwise 0. Relevance is not assessed. |
| Education | 5% | 100 if an education section contains text, otherwise 0. Requirements are not assessed. |

Each component score is returned in `match_breakdown`. If the transformer is unavailable, semantic similarity falls back to token cosine similarity; `semantic_match_source` reports `token-overlap fallback`, so the fallback is not presented as model output. With no job description, job compatibility remains a resume-skill-count heuristic capped at 100 and matching component scores are not available.

### Estimated ATS compatibility

The API returns `ats_analysis` with an `Estimated ATS Compatibility` label, numeric score, per-check status/evidence, recommendations, formatting-assessment note, and disclaimer. Checks cover contact details, standard sections, a skills heading, detected job skills when present, and a short list of generic/weak phrases. Weights are deterministic; when a job description has detected skills, job-skill coverage is included. Without detected job skills, the other check weights are normalized to the remaining total.

The parser only receives extracted text, so ATS analysis does **not** currently inspect columns, tables, images, fonts, visual hierarchy, or layout. The score does not predict any proprietary ATS result.

### Extraction

- Sections are recognized from exact heading names and aliases; text is collected until the next recognized heading.
- Email, phone, LinkedIn, GitHub, and a general URL are found with regular expressions. Name uses a first-line fallback.
- Skills are matched against the finite `SKILL_LIBRARY`; records include canonical skill, category, source evidence, and a fixed confidence value.
- Education, experience, projects, and certifications are currently section text lines, not normalized entities such as institution, dates, employer, or role.
- Summary is the first 400 characters of normalized resume text.

## Run locally on Windows

### Requirements

- Python 3.10 or newer (Python 3.11 is a reasonable default for the ML dependency stack).
- Node.js and npm.
- Internet access on first semantic-model use if the configured Hugging Face model is not cached. Subsequent requests reuse the process-loaded model.

### Backend

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example .env
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell activation is restricted, call `\.venv\Scripts\python.exe` directly. The API is at `http://127.0.0.1:8000`; OpenAPI docs are at `http://127.0.0.1:8000/docs`.

### Frontend

Open another terminal at the repository root:

```powershell
Copy-Item frontend\.env.example frontend\.env
Set-Location frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`. Set `VITE_API_BASE_URL` in `frontend/.env` to point to a different API URL.

## Configuration

The backend loads `.env` from the repository root, then `backend/.env` (existing root values take precedence). Copy `backend/.env.example` to either location and set only the values needed for the environment.

| Variable | Default | Use |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./resume_scanner.db` | SQLAlchemy database URL. Tables are created at API startup. |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face sentence-transformer used for semantic matching. |
| `MAX_FILE_SIZE` | `10485760` | Maximum upload size in bytes; default 10 MiB. |
| `UPLOAD_DIR` | `<repo>/tmp/uploads` | Destination for explicit `/api/resume/upload` files. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed browser origins. |
| `AI_PROVIDER` | empty | Optional `openai` or `gemini`; unset uses local fallback. |
| `AI_API_KEY` | empty | Provider secret, kept in backend environment only. |
| `AI_MODEL` | `gpt-4o-mini` | OpenAI model; Gemini uses this if it begins with `gemini-`, otherwise `gemini-2.0-flash`. |
| `APP_ENV` | `development` | Environment label. |
| `SECRET_KEY` | development placeholder | HMAC token-signing key. Production startup rejects the placeholder or values shorter than 32 characters. |

The AI provider calls require outbound network access. The API key must not be placed in a `VITE_` variable or frontend source.

## API

All paths are prefixed with `/api`. Errors use FastAPI JSON `detail` messages.

| Method | Path | Input | Result |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Service status. |
| `POST` | `/auth/register` | JSON `{"email":"...","password":"at-least-10-characters"}` | Creates an account and returns a bearer token. |
| `POST` | `/auth/login` | Same JSON fields | Checks credentials and returns a 12-hour bearer token. |
| `GET` | `/auth/me` | Bearer token | Returns the current account ID and email. |
| `DELETE` | `/auth/me` | Bearer token | Deletes the current account and its analysis records. Separately stored uploaded files are not removed. |
| `POST` | `/resume/upload` | Multipart `file` | Validates PDF/DOCX and saves under a generated name in `UPLOAD_DIR`. This endpoint does not analyze the file. |
| `POST` | `/resume/analyze` | Multipart `file`, optional `job_description` | Parses, scores, persists, and returns analysis including `analysis_id`, scores, ATS checks, match breakdown, skills, issues, and recommendations. Used by the UI. |
| `POST` | `/job/analyze` | JSON `{"job_description":"..."}` | Returns detected skill records and a description preview. |
| `POST` | `/match` | Query fields `resume_text`, `job_description` | Returns transformer semantic similarity (or named fallback), token keyword similarity, and text previews. |
| `GET` | `/resumes/history` | None | Recent saved analysis metadata and scores. |
| `DELETE` | `/resumes/history` | None | Clears all saved analysis records. Separately stored uploaded files are untouched. |
| `GET` | `/resume/{analysis_id}` | Path ID | Saved analysis result JSON. |
| `DELETE` | `/resume/{analysis_id}` | Path ID | Deletes the saved analysis record. |
| `GET` | `/report/{analysis_id}` | Path ID | Downloads a generated `application/pdf` analysis report. |
| `GET` | `/settings` | None | Returns non-secret AI-provider/model status and storage notes. |
| `POST` | `/resume/compare` | JSON `{"first_analysis_id":1,"second_analysis_id":2}` | Score deltas plus added/removed skills and sections. |
| `POST` | `/resume/improve-summary` | JSON `{"text":"..."}` | Summary wording suggestion with `mode`, provider, and notice. |
| `POST` | `/resume/improve-bullet` | JSON `{"text":"..."}` | Bullet wording suggestion with `mode`, provider, and notice. |

The improvement endpoints reject empty text and inputs above 10,000 characters. Provider suggestions should be reviewed for factual accuracy. All endpoints except health and authentication operations require `Authorization: Bearer <token>`; account data is scoped to the authenticated user.

## Data, privacy, and security

- The analysis endpoint processes the uploaded file in a unique temporary file and deletes it after parsing, including parser failures. It stores the resulting analysis JSON in SQLite; that result includes extracted details, section text, and a short resume summary.
- The separate upload endpoint retains its uploaded file under `UPLOAD_DIR`. There is currently no file retrieval or automated retention/cleanup endpoint for those uploads.
- Passwords are stored as salted scrypt hashes. Signed bearer tokens expire after 12 hours; the browser stores them in `sessionStorage` for the current tab session. Use HTTPS in any deployment.
- Analysis history is scoped by account. Records created before account ownership was added remain unassigned and are not exposed to newly registered accounts.
- Password reset, email verification, MFA, distributed login throttling, token revocation, and automated retention remain unimplemented; use a security review before public deployment.
- Upload extension, size, PDF signature, and DOCX archive/document checks run server-side. These checks do not make arbitrary documents risk-free.
- CORS defaults to the two local Vite origins and can be configured with `CORS_ORIGINS`.
- API keys remain in backend configuration. Analysis errors return a generic server message instead of raw parser exceptions.
- No legal privacy or ATS compliance guarantee is made. Operators are responsible for informing users about processing, storage, external AI providers, and retention.

## Tests and checks

Run backend tests from the `backend/` folder:

```powershell
python -m pytest tests -q
```

Or from the repository root:

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend/tests -q
```

Run frontend checks from `frontend/`:

```powershell
npm run lint
npm run build
```

Current backend tests cover normalization, section/skill detection and aliases, negation filtering, required/preferred priority, weighted skill scoring, concrete recommendations, role overlap, token similarity, ATS checks, file validation, labeled AI fallback, password/token handling, account registration, per-user history isolation/clearing, secret-free settings status, and generated PDF readability. There is not yet comprehensive upload/API integration coverage, PDF/DOCX parser-fixture coverage, performance testing, or accessibility automation.

## Known limitations

- Scanned/image-only PDFs are not OCR-processed because Tesseract is not installed/configured in this runtime. The parser returns a clear no-text extraction error instead of fabricated results.
- `.doc` is not supported; only PDF and DOCX are accepted by the current UI and analysis API.
- Contact, name, sections, and skills use heuristics and a finite taxonomy. Career history, education, projects, certifications, achievements, languages, and publications are not fully normalized.
- Required/preferred skill priority is a local wording heuristic, not full job-requirement parsing. Skills are extracted from a fixed vocabulary, so unknown terms are missed and a detected term is not proof of proficiency.
- Experience, project, and education match components currently test section presence, not relevance or quality.
- ATS formatting/layout checks, full grammar/spelling analysis, OCR, and calibrated hiring scores are not implemented.
- Transformer model download/loading may be slow or fail without network/cache; token overlap is then used and labeled.
- Account authentication is local email/password with bearer sessions; account recovery, MFA, distributed brute-force throttling, and scheduled retention remain unimplemented.
- Optional AI wording improvement is limited to summary and bullet text. It is not a full resume-generation service and cannot guarantee that provider output preserves every fact.
- Full profile, password reset, and account recovery workflows are not implemented.

Supporting design notes live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md), [docs/NLP_PIPELINE.md](docs/NLP_PIPELINE.md), [docs/SCORING_LOGIC.md](docs/SCORING_LOGIC.md), and [docs/DEEP_LEARNING.md](docs/DEEP_LEARNING.md). This README describes active behavior; design notes may include future directions.