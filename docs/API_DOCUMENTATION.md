# API Documentation

## Health
GET /api/health

Returns service status.

## Upload resume
POST /api/resume/upload

Accepts a multipart file upload.

Supported file types: PDF, DOCX, DOC (if supported by the runtime).

## Analyze resume
POST /api/resume/analyze

Accepts a file upload and optional job description.

## Analyze job description
POST /api/job/analyze

Accepts a JSON body with `job_description`.

## Match resume to job
POST /api/match

Accepts `resume_text` and `job_description` values in form data.
