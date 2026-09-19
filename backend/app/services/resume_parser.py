import re
from typing import Any

from app.services.section_detector import detect_sections
from app.services.job_matcher import compute_similarity
from app.services.skill_extractor import extract_skills


def extract_contact(text: str) -> dict[str, str]:
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    linkedin = re.search(r"https?://(?:www\.)?linkedin\.com/in/[^\s]+", text, re.I)
    github = re.search(r"https?://(?:www\.)?github\.com/[^\s]+", text, re.I)
    portfolio = re.search(r"https?://[^\s]+", text, re.I)

    return {
        "name": "",
        "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "",
        "linkedin": linkedin.group(0) if linkedin else "",
        "github": github.group(0) if github else "",
        "portfolio": portfolio.group(0) if portfolio else "",
        "location": "",
    }


def build_resume_summary(text: str, job_description: str = "") -> dict[str, Any]:
    source_text = text.strip()
    clean_text = re.sub(r"\s+", " ", source_text).strip()
    sections = detect_sections(source_text)
    skills = extract_skills(source_text)
    job_skills = extract_skills(job_description)
    contact = extract_contact(source_text)
    resume_skill_names = {item["skill"] for item in skills}
    job_skill_names = {item["skill"] for item in job_skills}
    matched_skills = sorted(resume_skill_names & job_skill_names)
    missing_skills = sorted(job_skill_names - resume_skill_names)
    similarity = compute_similarity(clean_text, job_description)
    skill_match = round(len(matched_skills) / len(job_skill_names) * 100) if job_skill_names else 0
    keyword_match = round(similarity * 100)
    compatibility = round(skill_match * 0.55 + keyword_match * 0.45) if job_description.strip() else round(min(100, len(skills) * 10))
    first_line = next((line.strip() for line in source_text.splitlines() if line.strip()), "")
    detected_name = first_line if first_line and "@" not in first_line and len(first_line.split()) <= 5 else ""
    recommendations = []
    issues = []
    if missing_skills:
        recommendations.append(f"Consider adding evidence for: {', '.join(missing_skills)}.")
    if "experience" not in sections:
        issues.append("No experience section was detected.")
        recommendations.append("Add an Experience section with measurable achievements.")
    if "education" not in sections:
        issues.append("No education section was detected.")
    if not contact.get("email"):
        issues.append("No email address was detected.")
    result = {
        "resume": {
            "name": contact.get("name") or detected_name or "Unknown Candidate",
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "skills": [item["skill"] for item in skills],
            "sections_detected": list(sections.keys()),
            "education": sections.get("education", []),
            "experience": sections.get("experience", []),
            "projects": sections.get("projects", []),
            "certifications": sections.get("certifications", []),
        },
        "job": {
            "skills": job_skills,
            "requirements": [],
        },
        "scores": {
            "compatibility": compatibility,
            "semantic_match": keyword_match,
            "skill_match": skill_match,
            "keyword_match": keyword_match,
            "experience_match": 100 if "experience" in sections else 0,
            "education_match": 100 if "education" in sections else 0,
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendations or ["Your resume has been parsed successfully. Add a job description for targeted matching."],
        "issues": issues,
        "summary": clean_text[:400],
    }
    if not job_description.strip():
        result["message"] = "Job matching unavailable because no Job Description was provided."
    return result
