# NLP Pipeline

## Stages
1. Text extraction from PDF or DOCX
2. Unicode normalization and whitespace cleanup
3. Section detection using heading pattern normalization
4. Regular-expression contact extraction and heading-based section text collection
5. Skill matching against a finite curated taxonomy, with aliases, negation checks, source-line evidence, section-aware confidence, and canonical names
6. Job skill priority inferred from nearby required/preferred wording
7. Semantic comparison with cached sentence-transformer embeddings and full-vocabulary token-cosine fallback
8. Evidence-backed skill gaps and resume-edit recommendations

## Important design choices
- The project does not aggressively remove stopwords from resume text because resumes contain important terms such as "not", "with", "without", technical abbreviations, and company names.
- Different preprocessing is used for different tasks:
  - extraction: light cleanup and section handling
  - embedding: normalized full resume and job-description text
  - ATS analysis: keyword, section, contact, and skill checks on extracted text
- A detected skill means a taxonomy term was found with evidence; it does not prove proficiency. Explicit negative phrases near a mention are filtered.
- Skill-match weighting is deterministic: required job terms weigh twice as much as unqualified mentions, while preferred terms weigh half as much. Required/preferred classification is a phrase heuristic, not a full job-requirement parser.
- Education and experience content remain section text lines; the pipeline does not normalize institutions, employers, titles, dates, or durations into structured entities.

## Section normalization
The system maps variants such as "Professional Experience", "Work History", and "Employment" into a normalized EXPERIENCE section.
