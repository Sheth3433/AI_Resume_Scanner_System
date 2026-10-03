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

- Single-page, responsive scanner with Analyze, Results, History, Improve, and Settings navigation; users can choose a supported IT role, paste a job description, or provide both.
- Email/password registration and sign-in, 12-hour signed bearer sessions, sign-out, and account-isolated analysis history.
- Five failed sign-ins per account within a 15-minute window are throttled by the current API process.
- Drag-and-drop and keyboard-accessible file picker for PDF and DOCX only.
- Client-side extension, empty-file, and 10 MiB size checks; the backend repeats validation and checks document signatures/structure.
- Selected filename and size preview, remove/replace action, optional job-description field, progress status, API error messages, and empty states.
- Results for overall compatibility, the job-targeted 60/40 semantic/exact-skill ATS estimate, skill match, keyword similarity, and separate document-readiness checks.
- Matched skills, skills not detected in the resume, extracted contact/section details, findings, and recommendations.
- ATS checks include supporting evidence and clearly mark document layout as unassessed.
- History supports open, delete, clear-all, PDF download, and compare-two-analyses workflows, with score changes and added/removed skills and sections.
- Downloadable PDF analysis report with candidate details, scores, skills, ATS checks, recommendations, and heuristic limitations.
- Role profiles cover Backend, Frontend, Full Stack, Python/Java, Data, AI/ML, DevOps, Mobile, QA Automation, Cybersecurity, Cloud, and Database jobs. Alternative stacks are grouped so competing languages/frameworks are not all treated as required.
- Role fit checks exact skill evidence and project lines. It distinguishes uncovered role categories from optional stack alternatives and does not tell users to claim skills they lack.
- Education, experience, project, and certification section lines are conservatively converted into structured records with source evidence and `Not detected` values for unknown fields.
- Scanned PDFs use Tesseract OCR when installed and configured; the backend returns a setup-specific error when the executable is unavailable.
- Settings/Privacy screen shows non-secret provider status, storage/retention notes, and clear-history action.
- Summary and bullet wording suggestions. Provider output is identified as AI-assisted; the local fallback is identified as rule-based.
- Neutral responsive layout, visible keyboard focus, and reduced-motion support.

### Backend analysis

- FastAPI API with health, upload, analysis, job-analysis, matching, history, comparison, and wording-improvement endpoints.
- PyMuPDF PDF extraction/OCR fallback and `python-docx` DOCX paragraph extraction, whitespace cleanup, and safe unique temporary analysis files.
- PDF signature and DOCX archive/document validation, supported-extension and size checks, and clean errors for unreadable, empty, protected, or textless files.
- Heading-based section detection; regular-expression contact detection; alias-aware skills from the maintained in-code taxonomy.
- Skill records contain source line, detected section, and section-weighted confidence; common aliases are canonicalized and explicit negative mentions are ignored.
- Job skills are classified as required, preferred, or mentioned from nearby wording; required skills count more than preferred/unspecified skills in the skill-match subscore.
- `GET /api/roles` returns the supported IT role profiles; `POST /api/resume/analyze` accepts an optional `target_role` field.
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
| [backend/app/services/role_profiles.py](backend/app/services/role_profiles.py) | Curated IT role groups, interchangeable skill alternatives, and role/project-fit calculations. |
| [backend/app/services/structured_extractor.py](backend/app/services/structured_extractor.py) | Conservative education, experience, project, and certification records with evidence. |
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

### Estimated ATS score

When a job description or IT role is selected, `scores.ats_compatibility` uses:

```text
ATS score = 60% x semantic similarity + 40% x weighted exact skill coverage
```

Semantic cosine is clamped to `[0, 1]`; exact skill coverage weights required job terms as 2, ordinary mentions as 1, and preferred terms as 0.5. For role profiles, one detected skill in an alternative group satisfies that role category. If both inputs are selected, exact coverage combines 60% JD skill coverage and 40% role-group coverage. The response returns these source components in `skill_match_basis`. If no JD terms match the finite taxonomy, the pasted-code formula's neutral 100% exact component is used and the check is labeled not assessed. Without a target job/role, ATS falls back to document-readiness checks and the UI labels that basis explicitly.

`ats_analysis.document_readiness_score` stays separate, with per-check evidence for contact details, standard sections, skill heading, job/role skill evidence, and generic phrases. Extracted text cannot reliably inspect columns, tables, images, fonts, visual hierarchy, or layout. Neither score predicts a proprietary ATS system.

### Extraction

- Sections are recognized from exact heading names and aliases; text is collected until the next recognized heading.
- Email, phone, LinkedIn, GitHub, and a general URL are found with regular expressions. Name uses a first-line fallback.
- Skills are matched against the finite `SKILL_LIBRARY`; records include canonical skill, category, source evidence, and a fixed confidence value.
- Education, experience, projects, and certifications are emitted as conservative structured records with raw evidence; dates, titles, institutions, fields, and issuers are parsed only when explicit and otherwise use `Not detected`.
- Summary is the first 400 characters of normalized resume text.

## Run locally on Windows

### Requirements

- Python 3.10 or newer (Python 3.11 is a reasonable default for the ML dependency stack).
- Node.js and npm.
- Internet access on first semantic-model use if the configured Hugging Face model is not cached. Subsequent requests reuse the process-loaded model.
- Optional Tesseract OCR executable and English language data for scanned/image-only PDFs. Set `TESSERACT_CMD` when it is not on `PATH`.

### Install and run both services

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example .env
npm install
npm --prefix frontend install
npm run dev
```

The root command starts FastAPI at `http://127.0.0.1:8000` and Vite at `http://127.0.0.1:5173`; OpenAPI docs are at `http://127.0.0.1:8000/docs`. Vite hot reload is enabled. The backend launcher uses the repository `.venv` and intentionally avoids Uvicorn's child-process reload mode, which had interrupted the combined Windows terminal; restart `npm run dev` after backend source changes.

Run only one service from the repository root with `npm run backend` or `npm run frontend`. If PowerShell activation is restricted, the launcher still calls `\.venv\Scripts\python.exe` directly when present.

The frontend API base defaults to `http://localhost:8000/api`; set `VITE_API_BASE_URL` in `frontend/.env` to change it.

### Scanned PDF OCR

The Python `pytesseract` wrapper is installed with backend dependencies, but the Tesseract executable is a separate system install. Install Tesseract OCR for Windows, then either add `tesseract.exe` to `PATH` or set `TESSERACT_CMD` in `.env` to its full path. The backend OCRs up to `OCR_MAX_PAGES` pages at a time. In this workspace the executable is currently absent, so scanned PDFs return a clear setup message until it is installed.

## Configuration

The backend loads `.env` from the repository root, then `backend/.env` (existing root values take precedence). Copy `backend/.env.example` to either location and set only the values needed for the environment.

| Variable | Default | Use |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./resume_scanner.db` | SQLAlchemy database URL. Tables are created at API startup. |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face sentence-transformer used for semantic matching. |
| `MAX_FILE_SIZE` | `10485760` | Maximum upload size in bytes; default 10 MiB. |
| `TESSERACT_CMD` | empty | Full path to `tesseract.exe` when the OCR engine is not available on `PATH`. |
| `OCR_LANGUAGE` | `eng` | Tesseract language code; corresponding trained data must be installed. |
| `OCR_MAX_PAGES` | `20` | Maximum PDF pages passed to OCR. |
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
| `POST` | `/resume/analyze` | Multipart `file`, optional `job_description`, optional `target_role` | Parses, scores, persists, and returns analysis including target-role groups, project evidence, structured fields, ATS details, and recommendations. |
| `GET` | `/roles` | Bearer token | Lists supported IT role profiles and descriptions for the role selector. |
| `POST` | `/job/analyze` | JSON `{"job_description":"..."}` | Returns detected skill records and a description preview. |
| `POST` | `/match` | Query fields `resume_text`, `job_description` | Returns transformer semantic similarity (or named fallback), token keyword similarity, and text previews. |
| `GET` | `/resumes/history` | None | Recent saved analysis metadata and scores. |
| `DELETE` | `/resumes/history` | None | Clears all saved analysis records. Separately stored uploaded files are untouched. |
| `GET` | `/resume/{analysis_id}` | Path ID | Saved analysis result JSON. |
| `DELETE` | `/resume/{analysis_id}` | Path ID | Deletes the saved analysis record. |
| `GET` | `/report/{analysis_id}` | Path ID | Downloads a generated `application/pdf` analysis report. |
| `GET` | `/settings` | None | Returns non-secret AI/OCR availability, model status, and storage notes. |
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

Current backend tests cover normalization, section/skill detection and aliases, negation filtering, required/preferred priority, 60/40 ATS math including unknown-skill JD fallback, IT role alternatives/project matching, structured education/experience/project extraction, OCR fallback and missing-executable messaging, recommendations, token similarity, file validation, AI fallback, password/session security, account isolation, settings, and PDF report readability. Full uploaded PDF/DOCX parser fixtures, browser accessibility automation, and performance testing remain limited.

## Known limitations

- Scanned/image-only PDFs use Tesseract OCR when its executable and language data are installed. Tesseract is absent in this workspace; `winget` found the package but offered no applicable user-scope installer, so actual OCR text recognition is not verified here.
- `.doc` is not supported; only PDF and DOCX are accepted by the current UI and analysis API.
- Contact, name, sections, and skills use heuristics and a finite IT taxonomy. Education, experience, projects, and certifications now have conservative structured records, but dates/titles/institutions and other fields are heuristic and may remain `Not detected`.
- Required/preferred skill priority is a local wording heuristic, not full job-requirement parsing. Skills are extracted from a fixed vocabulary, so unknown terms are missed and a detected term is not proof of proficiency.
- Role profiles are curated examples, not live job-posting data or a guarantee that every employer uses the same requirements. Pasted job descriptions should be preferred for a specific opening.
- The legacy overall compatibility score still includes section-presence experience/project/education components; these do not evaluate relevance, duration, or quality. The new selected-role score separately checks grouped skills and project evidence.
- ATS formatting/layout checks, full grammar/spelling analysis, and calibrated hiring scores are not implemented. OCR fallback is implemented but requires the external Tesseract executable.
- Transformer model download/loading may be slow or fail without network/cache; token overlap is then used and labeled.
- Account authentication is local email/password with bearer sessions; account recovery, MFA, distributed brute-force throttling, and scheduled retention remain unimplemented.
- Optional AI wording improvement is limited to summary and bullet text. It is not a full resume-generation service and cannot guarantee that provider output preserves every fact.
- Full profile, password reset, and account recovery workflows are not implemented.

Supporting design notes live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md), [docs/NLP_PIPELINE.md](docs/NLP_PIPELINE.md), [docs/SCORING_LOGIC.md](docs/SCORING_LOGIC.md), and [docs/DEEP_LEARNING.md](docs/DEEP_LEARNING.md). This README describes active behavior; design notes may include future directions.