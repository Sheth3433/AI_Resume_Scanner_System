# NLP Pipeline

## Stages
1. Text extraction from PDF or DOCX
2. Unicode normalization and whitespace cleanup
3. Section detection using heading pattern normalization
4. Structured extraction of contacts, experience, education, and skills
5. Skill matching against a curated taxonomy
6. Semantic comparison with embeddings and lexical score features

## Important design choices
- The project does not aggressively remove stopwords from resume text because resumes contain important terms such as "not", "with", "without", technical abbreviations, and company names.
- Different preprocessing is used for different tasks:
  - extraction: light cleanup and section handling
  - embedding: normalized chunks while preserving context
  - ATS analysis: keyword and skill coverage on structured tokens

## Section normalization
The system maps variants such as "Professional Experience", "Work History", and "Employment" into a normalized EXPERIENCE section.
