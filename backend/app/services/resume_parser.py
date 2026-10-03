import re
from typing import Any

from app.services.section_detector import detect_sections
from app.services.job_matcher import compute_semantic_similarity, compute_similarity
from app.services.skill_extractor import extract_skills
from app.services.skill_extractor import classify_job_skills
from app.services.ats_scorer import analyze_ats
from app.services.recommendation_engine import build_recommendation_details
from app.services.role_recommender import recommend_roles
from app.services.role_profiles import ROLE_PROFILES, analyze_role_fit
from app.services.structured_extractor import extract_structured_resume


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


def build_resume_summary(text: str, job_description: str = "", target_role: str | None = None) -> dict[str, Any]:
    source_text = text.strip()
    clean_text = re.sub(r"\s+", " ", source_text).strip()
    sections = detect_sections(source_text)
    skills = extract_skills(source_text)
    job_skills = classify_job_skills(job_description, extract_skills(job_description))
    contact = extract_contact(source_text)
    selected_role = None
    if target_role and target_role.strip():
        selected_role = next((role for role in ROLE_PROFILES if role.casefold() == target_role.strip().casefold()), None)
        if selected_role is None:
            raise ValueError("Unsupported IT target role. Load the available options from GET /api/roles.")
    structured = extract_structured_resume(sections)
    role_analysis = analyze_role_fit(selected_role, skills, sections)
    related_project_skills = {
        item["evidence"]: item["matched_skills"]
        for item in (role_analysis or {}).get("related_projects", [])
    }
    for project in structured["projects"]:
        project["matched_skills"] = related_project_skills.get(project["evidence"], [])
    resume_skill_names = {item["skill"] for item in skills}
    job_skill_names = {item["skill"] for item in job_skills}
    matched_skills = sorted(resume_skill_names & job_skill_names)
    if role_analysis and not job_description.strip():
        role_matched_skills = {
            skill
            for group in role_analysis["skill_groups"]
            for skill in group["matched_skills"]
        }
        matched_skills = sorted(role_matched_skills)
    missing_skills = sorted(job_skill_names - resume_skill_names)
    importance_weights = {"required": 2.0, "mentioned": 1.0, "preferred": 0.5}
    total_skill_weight = sum(importance_weights.get(item["importance"], 1.0) for item in job_skills)
    matched_skill_weight = sum(
        importance_weights.get(item["importance"], 1.0)
        for item in job_skills
        if item["skill"] in resume_skill_names
    )
    job_skill_ratio = matched_skill_weight / total_skill_weight if total_skill_weight else None
    role_skill_ratio = role_analysis["required_groups_met"] / role_analysis["total_required_groups"] if role_analysis and role_analysis["total_required_groups"] else None
    if job_skill_ratio is not None and role_skill_ratio is not None:
        skill_ratio = job_skill_ratio * 0.6 + role_skill_ratio * 0.4
    elif job_skill_ratio is not None:
        skill_ratio = job_skill_ratio
    elif role_skill_ratio is not None:
        skill_ratio = role_skill_ratio
    else:
        skill_ratio = 1.0 if job_description.strip() else 0.0
    has_job_target = bool(job_description.strip() or role_analysis)
    skill_match = round(skill_ratio * 100) if has_job_target else 0
    target_text = job_description.strip()
    if not target_text and role_analysis:
        group_descriptions = " ".join(
            f"{group['group']}: {', '.join(group['skills'])}." for group in role_analysis["skill_groups"]
        )
        target_text = f"{role_analysis['role']}. {role_analysis['description']} {group_descriptions}"
    semantic_similarity, semantic_source = compute_semantic_similarity(clean_text, target_text)
    keyword_similarity = compute_similarity(clean_text, target_text)
    semantic_component = max(0.0, min(1.0, semantic_similarity))
    semantic_match = round(semantic_component * 100)
    keyword_match = round(keyword_similarity * 100)
    ats_analysis = analyze_ats(
        source_text,
        sections,
        contact,
        job_skills,
        semantic_similarity=semantic_component if has_job_target else None,
        skill_match_ratio=skill_ratio if has_job_target else None,
        target_role=selected_role,
    )
    experience_match = 100 if sections.get("experience") else 0
    projects_match = 100 if sections.get("projects") else 0
    education_match = 100 if sections.get("education") else 0
    match_breakdown = {
        "semantic": {"weight": 30, "score": semantic_match},
        "skills": {"weight": 30, "score": skill_match},
        "keywords": {"weight": 15, "score": keyword_match},
        "experience": {"weight": 10, "score": experience_match},
        "projects": {"weight": 10, "score": projects_match},
        "education": {"weight": 5, "score": education_match},
    }
    compatibility = round(sum(part["weight"] * part["score"] for part in match_breakdown.values()) / 100) if has_job_target else round(min(100, len(skills) * 10))
    first_line = next((line.strip() for line in source_text.splitlines() if line.strip()), "")
    detected_name = first_line if first_line and "@" not in first_line and len(first_line.split()) <= 5 else ""
    recommendation_details = build_recommendation_details(
        sections,
        contact,
        skills,
        job_skills,
        matched_skills,
        missing_skills,
        ats_analysis["weak_phrases"],
        role_analysis,
    )
    recommendations = [f"{item['title']}. {item['action']}" for item in recommendation_details]
    issues = []
    if "experience" not in sections:
        issues.append("No experience section was detected.")
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
            "skill_details": skills,
            "sections_detected": list(sections.keys()),
            "education": structured["education"],
            "experience": structured["experience"],
            "projects": structured["projects"],
            "certifications": structured["certifications"],
        },
        "job": {
            "description": job_description,
            "skills": job_skills,
            "requirements": [],
        },
        "scores": {
            "compatibility": compatibility,
            "ats_compatibility": ats_analysis["score"],
            "semantic_match": semantic_match,
            "skill_match": skill_match,
            "keyword_match": keyword_match,
            "experience_match": experience_match,
            "projects_match": projects_match,
            "education_match": education_match,
        },
        "match_breakdown": match_breakdown if has_job_target else {},
        "skill_match_basis": {
            "job_description": round(job_skill_ratio * 100) if job_skill_ratio is not None else None,
            "role_profile": round(role_skill_ratio * 100) if role_skill_ratio is not None else None,
            "combined_weights": {"job_description": 60, "role_profile": 40} if job_skill_ratio is not None and role_skill_ratio is not None else None,
        },
        "semantic_match_source": semantic_source,
        "matched_skills": matched_skills,
        "matched_skill_details": [item for item in skills if item["skill"] in matched_skills],
        "missing_skills": missing_skills,
        "missing_skill_details": [item for item in job_skills if item["skill"] in missing_skills],
        "recommendations": recommendations or ["Your resume has been parsed successfully. Add a job description for targeted matching."],
        "recommendation_details": recommendation_details,
        "role_recommendations": recommend_roles([item["skill"] for item in skills]),
        "role_analysis": role_analysis,
        "issues": issues,
        "ats_analysis": ats_analysis,
        "summary": clean_text[:400],
    }
    if not job_description.strip() and not selected_role:
        result["message"] = "Job matching unavailable because no Job Description was provided."
    elif selected_role and not job_description.strip():
        result["message"] = f"Matched against the {selected_role} role profile. Skill alternatives are grouped; optional tools are not required."
    return result
