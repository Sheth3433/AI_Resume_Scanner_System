# API Documentation

All routes are mounted under `/api`. Validation and expected errors return a JSON `detail` field.

## Authentication

- `POST /api/auth/register` accepts an email and a password of 10–128 characters, stores a salted scrypt password hash, and returns a bearer token.
- `POST /api/auth/login` verifies the password hash and returns a signed bearer token with a 12-hour expiry.
- `GET /api/auth/me` returns the current account for a valid bearer token.
- `DELETE /api/auth/me` deletes that account and its analysis records. Separately stored files from `/api/resume/upload` are not removed.

All application routes other than health and authentication routes require `Authorization: Bearer <access_token>`. Analysis history, reports, comparison, and clearing are scoped to the authenticated account. Configure a random `SECRET_KEY` of at least 32 characters for production. Five failed logins for an email within 15 minutes are throttled in a single process; this in-memory limiter is not shared between workers. Password recovery, token refresh/revocation, email verification, and MFA are not implemented.

## Health

`GET /api/health` returns service status.

## Resume upload and analysis

`POST /api/resume/upload` accepts multipart `file`. Only PDF and DOCX are accepted. The endpoint validates the size and document signature, stores the document under a generated UUID filename in `UPLOAD_DIR`, and returns the original filename, byte count, and status. The stored file is not automatically removed.

`POST /api/resume/analyze` accepts multipart `file`, optional `job_description`, and optional `target_role` (one of the role values listed by `GET /api/roles`). It extracts text, analyzes the resume, saves the result record, and returns an `analysis_id` with resume/job details, structured section records, role-fit groups/project evidence, scores, `match_breakdown`, `semantic_match_source`, `ats_analysis`, skills, issues, and recommendations. Analysis input files are temporary and deleted after parsing. The result JSON is persisted in SQLite.

`GET /api/roles` returns the curated IT role-profile catalogue. Each role groups interchangeable technologies (for example, alternative backend languages) so all alternatives are not marked required at once.

When a job description or target role is supplied, `scores.ats_compatibility` uses 60% semantic cosine similarity plus 40% weighted exact skill coverage. When both are provided, skill coverage combines 60% JD skill coverage and 40% role-group coverage; `skill_match_basis` reports those values. If the JD has no taxonomy matches, its formula-defined exact-skill component is neutral (100%) and the check says not assessed. `ats_analysis.document_readiness_score` is separate and covers text-level checks. If a PDF has no selectable text, the parser tries Tesseract OCR when the executable/language data are installed; otherwise it returns an explicit setup error.

## Job analysis and matching

`POST /api/job/analyze` accepts JSON:

```json
{"job_description": "..."}
```

Returns detected skill records and a short description preview. It does not claim to parse experience/education requirements.

`POST /api/match` accepts `resume_text` and `job_description` as query parameters. Returns transformer semantic similarity, its source (or token-overlap fallback), token cosine keyword similarity, and previews.

## Analysis history

- `GET /api/resumes/history` lists saved analysis metadata and scores.
- `DELETE /api/resumes/history` deletes all saved analysis records. Files separately saved by `/api/resume/upload` are not deleted.
- `GET /api/resume/{analysis_id}` returns one saved analysis JSON result.
- `DELETE /api/resume/{analysis_id}` deletes one saved analysis.
- `POST /api/resume/compare` accepts `{"first_analysis_id": 1, "second_analysis_id": 2}` and returns score deltas plus added/removed skills and sections.
- `GET /api/report/{analysis_id}` downloads a generated PDF with analysis scores, extracted details, skills, ATS findings, recommendations, and limitations.
- `GET /api/settings` returns non-secret AI provider configuration status and storage notes; it never returns an API key.

History operations are filtered by the bearer-authenticated account. Legacy rows without an owner are not returned to any account.

## Resume wording improvement

`POST /api/resume/improve-summary` and `POST /api/resume/improve-bullet` accept JSON `{ "text": "..." }`. Text must be non-empty and at most 10,000 characters. When `AI_PROVIDER` and `AI_API_KEY` are configured, the selected backend provider is called. Otherwise, or if the call fails, the response uses a labeled rule-based fallback. The response contains `improved_text`, `mode`, `provider`, and `notice`.