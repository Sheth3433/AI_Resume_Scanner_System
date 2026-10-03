# Scoring Logic

## Job-targeted ATS estimate

When a job description or IT target role is supplied, `scores.ats_compatibility` uses the requested hybrid formula:

```text
ATS score = 60% x semantic similarity + 40% x weighted exact skill coverage
```

The cosine semantic value is clamped to `[0, 1]`, converted to percent, and weighted at 60%. The skill component is exact canonical skill evidence weighted by JD priority: required = 2, unqualified mention = 1, preferred = 0.5. With a selected IT role and no pasted JD, the skill component is the share of role requirement groups met; any one listed alternative meets that group. If both a JD and role are supplied, skill coverage is 60% JD coverage plus 40% role-group coverage. The response exposes those source contributions in `skill_match_basis` and the ATS components in `ats_analysis`.

With no job description or target role, `ats_compatibility` falls back to document readiness. Its value is explicitly labeled in `ats_analysis.score_basis`; document readiness does not pretend to be a job match.

## Document readiness

`ats_analysis.document_readiness_score` checks contact data, standard section headings, a Skills heading, job/role skill evidence, and a small list of generic phrases. Each check includes evidence and status. Since this stage sees extracted text only, it cannot reliably measure columns, tables, images, font/formatting, or layout. Neither ATS score predicts a proprietary ATS result.

## Overall job compatibility

The existing `scores.compatibility` remains an explainable six-part match when a target is supplied:

| Component | Weight | Current measurement |
| --- | ---: | --- |
| Semantic | 30% | Sentence-transformer cosine or labeled token-overlap fallback. |
| Skills | 30% | Required/preferred weighted exact coverage, or selected-role groups when no JD is pasted. |
| Keywords | 15% | Full-vocabulary token-count cosine. |
| Experience | 10% | Presence of a detected Experience section. |
| Projects | 10% | Presence of a detected Projects section. |
| Education | 5% | Presence of a detected Education section. |

The section-presence dimensions do not evaluate relevance, duration, or quality. When no target is supplied, compatibility remains the existing resume-skill-count heuristic.

## IT role profiles

Supported roles are returned by `GET /api/roles`. Each profile has weighted requirement groups with alternative skills (for example, a programming-language group); it does not require every language/framework in a group. The role fit score uses 80% group coverage and up to 20% project evidence when a Projects section exists. Optional alternatives are shown separately from unmet required groups.

The role taxonomy and JD skill extraction are finite, evidence-based dictionaries, not live job-posting data. Matching requires text evidence and can miss unknown names or phrases; it does not infer proficiency from similarity alone.

## Similarity and fallback

The sentence-transformer is lazily loaded and cached. If loading/inference fails, token cosine is returned and named by `semantic_match_source`. Token keyword cosine uses the complete union vocabulary, so non-overlapping terms contribute to the vector magnitudes.