# Scoring Logic

## Explainable compatibility score
The final compatibility score is derived from multiple weighted subscores:
- Semantic similarity
- Skill match
- Keyword coverage
- Experience alignment
- Education alignment

The algorithm is kept transparent and config-driven rather than arbitrary.

## ATS-style interpretation
The project uses an ATS-style resume score to communicate compatibility in a way that is explainable and useful.

Example explanation:
- Strong Python and SQL match
- Good backend experience alignment
- Missing Docker requirement
- Experience section would benefit from measurable achievements

## Missing skills and recommendations
Missing skills are computed by comparing required skills from the job description to skills extracted from the resume. Recommendations are generated only for actual gaps or quality issues that can be proven from the extracted text.
