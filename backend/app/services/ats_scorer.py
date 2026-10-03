import re


def calculate_compatibility(similarity: float, details: dict) -> float:
    matched = len(details.get("matched_skills", []))
    missing = len(details.get("missing_skills", []))
    skill_total = matched + missing
    skill_coverage = matched / skill_total if skill_total else 0.0
    semantic_component = max(0.0, min(1.0, similarity))
    return round((0.6 * semantic_component + 0.4 * skill_coverage) * 100, 2)


def analyze_ats(
    text: str,
    sections: dict,
    contact: dict,
    job_skills: list[dict],
    *,
    semantic_similarity: float | None = None,
    skill_match_ratio: float | None = None,
    target_role: str | None = None,
) -> dict:
    normalized_text = text.lower()
    email_found = bool(contact.get("email"))
    phone_found = bool(contact.get("phone"))
    standard_sections = ("summary", "skills", "experience", "education", "projects")
    detected_sections = [section for section in standard_sections if sections.get(section)]
    resume_skills = {item["skill"].casefold() for item in _extract_skills(text)}
    required_skills = {item["skill"].casefold() for item in job_skills}
    matched_skills = sorted(resume_skills & required_skills)
    weak_phrases = ("worked on", "helped", "responsible for", "did", "made")
    weak_phrase_hits = [phrase for phrase in weak_phrases if re.search(rf"\b{re.escape(phrase)}\b", normalized_text)]
    checks = [
        {
            "name": "Contact information",
            "status": "pass" if email_found and phone_found else "warning",
            "detail": "Email and phone detected." if email_found and phone_found else "Email or phone information is missing.",
        },
        {
            "name": "Standard sections",
            "status": "pass" if len(detected_sections) >= 4 else "warning",
            "detail": f"Detected {len(detected_sections)} of 5 common sections: {', '.join(detected_sections) or 'none'}.",
        },
        {
            "name": "Skills section",
            "status": "pass" if sections.get("skills") else "warning",
            "detail": "A skills heading was detected." if sections.get("skills") else "No skills heading was detected.",
        },
        {
            "name": "Job-specific skills",
            "status": "not_assessed" if not job_skills and not target_role else "pass" if target_role and skill_match_ratio == 1 else "warning" if target_role and skill_match_ratio is not None else ("pass" if matched_skills else "warning"),
            "detail": "No skills from the current IT taxonomy were detected in this job description; its exact-skill component is neutral per the scoring rule." if not job_skills and not target_role and skill_match_ratio is not None else f"Role skill groups: {round((skill_match_ratio or 0) * 100)}% covered for {target_role}." if target_role and skill_match_ratio is not None else "Add a job description or select an IT role to assess job-specific skills." if not job_skills else f"Matched {len(matched_skills)} of {len(required_skills)} detected job skills.",
        },
        {
            "name": "Resume wording",
            "status": "warning" if weak_phrase_hits else "pass",
            "detail": f"Consider replacing generic phrases: {', '.join(weak_phrase_hits)}." if weak_phrase_hits else "No common weak phrases were detected.",
        },
    ]

    components = [
        (20, 100 if email_found and phone_found else (50 if email_found or phone_found else 0)),
        (30, round(len(detected_sections) / len(standard_sections) * 100)),
        (15, 100 if sections.get("skills") else 0),
        (15, max(0, 100 - len(weak_phrase_hits) * 25)),
    ]
    if job_skills:
        components.append((20, round(len(matched_skills) / len(required_skills) * 100) if required_skills else 0))
    document_readiness_score = round(sum(weight * value for weight, value in components) / sum(weight for weight, _ in components))
    has_job_target = semantic_similarity is not None and skill_match_ratio is not None
    semantic_component = max(0.0, min(1.0, semantic_similarity or 0.0))
    exact_skill_component = max(0.0, min(1.0, skill_match_ratio or 0.0))
    score = round((0.6 * semantic_component + 0.4 * exact_skill_component) * 100, 2) if has_job_target else document_readiness_score
    recommendations = [check["detail"] for check in checks if check["status"] == "warning"]
    return {
        "label": "Estimated ATS Match" if has_job_target else "Estimated ATS Readiness",
        "score": score,
        "document_readiness_score": document_readiness_score,
        "score_basis": "job_targeted" if has_job_target else "document_readiness",
        "formula": "60% semantic similarity + 40% weighted exact skill coverage" if has_job_target else "Document structure and content checks; no target job was supplied",
        "semantic_component": round(semantic_component * 100, 2) if has_job_target else None,
        "exact_skill_component": round(exact_skill_component * 100, 2) if has_job_target else None,
        "checks": checks,
        "recommendations": recommendations,
        "weak_phrases": weak_phrase_hits,
        "formatting_assessment": "Not assessed from extracted text; layout, columns, tables, and visual styling require document-level checks.",
        "disclaimer": "This estimate does not predict the behavior of any proprietary applicant tracking system.",
    }


def _extract_skills(text: str) -> list[dict]:
    from app.services.skill_extractor import extract_skills

    return extract_skills(text)
