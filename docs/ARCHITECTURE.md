# Architecture

## Runtime layers

- **Frontend:** React 19 and Vite single-page scanner, result dashboard, history/comparison controls, and summary/bullet improvement form.
- **API:** FastAPI routes under `/api`; Pydantic validates improvement and comparison payloads. Upload and analysis responses use explicit validation errors.
- **Document services:** PyMuPDF and `python-docx` extract text after extension/size/signature checks. A unique temporary file is removed after analysis.
- **Analysis services:** Normalization, heading-based section detection, regular-expression contact extraction, finite skill taxonomy, sentence-transformer embeddings, token-cosine fallback, hybrid score, ATS checks, and recommendations.
- **Persistence:** SQLAlchemy initializes the analysis table at app startup and stores analysis metadata plus result JSON in the configured database.
- **Authentication:** Email/password accounts use salted scrypt hashes and HMAC-SHA256 signed 12-hour bearer tokens. Resume analyses and history actions are owner-scoped; repeated failures are throttled in-process.
- **Optional provider integration:** OpenAI or Gemini is called only by wording-improvement routes when backend environment configuration is supplied. A labeled rule-based fallback is returned on missing configuration or provider failure.
- **User-facing support:** Exact skill-overlap role suggestions, evidence-backed recommendations, PDF report downloads, non-secret settings status, and analysis-history clearing.

## Analysis flow

1. The UI sends a PDF/DOCX and optional job description as multipart form data.
2. The API validates supported suffix, size, PDF signature or DOCX archive/document entry.
3. The parser writes bytes to a unique temporary file, extracts text, normalizes it, and removes the temporary file.
4. Heading/contact/skill heuristics produce extracted details.
5. A cached sentence-transformer produces semantic similarity; token cosine is the explicitly named fallback. Token keyword similarity is calculated separately.
6. The API combines semantic, skill, keyword, experience-section, project-section, and education-section scores and creates estimated ATS checks.
7. The result JSON and score metadata are saved to SQLite and returned to the UI.

## Boundaries

The extracted text is not a complete structured resume model. Visual layout, OCR, career chronology, full job-requirement parsing, account recovery/MFA, distributed login throttling, and automatic uploaded-file retention are not currently implemented. ATS scoring is an estimate and does not predict a proprietary system.