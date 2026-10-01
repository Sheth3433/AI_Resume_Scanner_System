# Scoring Logic

## Job compatibility score

When a job description is provided, the score is a deterministic weighted average:

| Component | Weight | Calculation |
| --- | ---: | --- |
| Semantic similarity | 30% | Sentence-transformer embeddings and normalized cosine similarity; token cosine is an explicitly named fallback. |
| Skills | 30% | Weighted coverage: required skill = 2, ordinary mention = 1, preferred skill = 0.5. Nearby wording determines priority heuristically. |
| Keywords | 15% | Token-count cosine similarity over the complete union vocabulary. |
| Experience | 10% | 100 if an experience section has text; otherwise 0. |
| Projects | 10% | 100 if a projects section has text; otherwise 0. |
| Education | 5% | 100 if an education section has text; otherwise 0. |

The response includes each component score and weight in `match_breakdown`. Section-presence dimensions do not evaluate relevance, seniority, duration, or quality. Skills are limited to the current skill taxonomy; aliases are canonicalized, explicit negation around a mention is filtered, and every retained match includes a source line and detected section. Required/preferred classification is a nearby-phrase heuristic, not a full requirements parser.

Without a job description, compatibility is `min(100, extracted_resume_skill_count * 10)`; this is a completeness-style heuristic, not a job match.

## Estimated ATS compatibility

The separate `ats_analysis` contains a deterministic estimate based on contact detection, standard section headings, a skills heading, generic weak phrases, and job-skill coverage when job skills are detected. It includes per-check evidence and warnings. The denominator is normalized when no job-skill check is available.

Because the parser analyzes extracted text, it does not currently detect columns, tables, image content, font/formatting problems, or layout reliably. This estimate does not predict the behavior of any proprietary applicant tracking system.

## Similarity and fallback

The sentence-transformer is lazily loaded and cached for the process. If model import, download, loading, or inference fails, the app calculates token cosine similarity and returns `semantic_match_source: "token-overlap fallback"`. This fallback is not represented as semantic model output. Keyword cosine uses all tokens from both sides; non-overlapping terms contribute to vector magnitudes.

## Recommendations

Recommendations are rule-based and reference detected missing job skills or absent sections/contact details. They do not represent a hiring decision or guarantee an interview outcome.