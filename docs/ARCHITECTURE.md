# Architecture

## System overview
The application follows a layered design: frontend UI, API layer, service layer, model layer, and persistence layer.

## Components
- Frontend: Vite React app for upload and dashboard
- Backend: FastAPI app for intake and analysis
- Services: document parsing, skill extraction, semantic similarity, scoring, recommendations
- Models: SQLAlchemy models for SQLite persistence
- Data: skill dictionaries and future training artifacts

## Processing flow
1. User uploads a resume file
2. File validation checks MIME/extension/size
3. Text extraction reads PDF or DOCX
4. Normalization and section detection prepare the resume
5. Structured information extraction captures contact and work history
6. Skill extraction matches to a maintained skill taxonomy
7. Pretrained transformer embeddings compare the resume and job description
8. Scoring engine produces explainable compatibility and ATS-style scores
9. Recommendation engine returns evidence-based suggestions

## Why pretrained models
The application uses pretrained transformer encoders instead of custom training per upload because the model already contains general-language semantics learned at large scale. This makes runtime inference fast and scalable for unseen resumes.
