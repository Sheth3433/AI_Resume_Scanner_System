from __future__ import annotations


def build_recommendation_details(
    sections: dict[str, list[str]],
    contact: dict[str, str],
    resume_skill_details: list[dict],
    job_skills: list[dict],
    matched_skills: list[str],
    missing_skills: list[str],
    weak_phrases: list[str],
    role_analysis: dict | None = None,
) -> list[dict[str, str]]:
    recommendations = []
    resume_skills = {item["skill"]: item for item in resume_skill_details}
    job_skill_map = {item["skill"]: item for item in job_skills}

    for skill_name in missing_skills:
        job_skill = job_skill_map[skill_name]
        importance = job_skill.get("importance", "mentioned")
        priority = {"required": "high", "mentioned": "medium", "preferred": "low"}.get(importance, "medium")
        importance_label = {"required": "required", "preferred": "preferred", "mentioned": "mentioned"}.get(importance, "mentioned")
        recommendations.append({
            "type": "skill_gap",
            "title": f"{skill_name} is {importance_label} in the job description, but not detected in your resume",
            "priority": priority,
            "skill": skill_name,
            "evidence": job_skill.get("evidence", ""),
            "action": f"Do not add it unless it reflects your real experience. If you have used {skill_name}, list it under Skills and support it with a truthful project or experience bullet; otherwise, build a small project before claiming it.",
        })

    if role_analysis:
        for group in role_analysis["unmet_groups"]:
            options = group["skills"]
            recommendations.append({
                "type": "role_skill_gap",
                "title": f"Add evidence for {group['group'].lower()} in your {role_analysis['role']} resume",
                "priority": "high",
                "skill": ", ".join(options[:4]),
                "evidence": f"No matching skill from this role group was detected: {', '.join(options)}.",
                "action": f"This role profile expects at least one of: {', '.join(options)}. If you have used one, add it to Skills and show it in a relevant project/experience bullet. These are alternatives, not a requirement to learn or claim every item.",
            })

    for skill_name in matched_skills:
        resume_skill = resume_skills.get(skill_name, {})
        source_section = resume_skill.get("source_section", "not_detected")
        if source_section != "skills":
            recommendations.append({
                "type": "skill_visibility",
                "title": f"Make {skill_name} easier to find",
                "priority": "medium",
                "skill": skill_name,
                "evidence": resume_skill.get("evidence", ""),
                "action": f"{skill_name} appears in your {source_section.replace('_', ' ')} text. Add it to a dedicated Skills section if it is a current, defensible skill, and keep the evidence in the relevant project or experience bullet.",
            })
        elif not any(
            skill_name.casefold() in line.casefold()
            for section in ("experience", "projects")
            for line in sections.get(section, [])
        ):
            recommendations.append({
                "type": "skill_evidence",
                "title": f"Add proof for {skill_name}",
                "priority": "medium",
                "skill": skill_name,
                "evidence": resume_skill.get("evidence", ""),
                "action": f"{skill_name} is listed in Skills but no related project/experience line was detected. Add one truthful bullet explaining where you used it and what you delivered; do not invent outcomes or metrics.",
            })

    if not sections.get("skills") and resume_skill_details:
        recommendations.append({
            "type": "section",
            "title": "Add a dedicated Skills section",
            "priority": "medium",
            "skill": "",
            "evidence": ", ".join(item["skill"] for item in resume_skill_details[:8]),
            "action": "Add a clear Skills heading near the top of the resume and list only skills supported by your experience or projects.",
        })
    if not sections.get("experience"):
        recommendations.append({
            "type": "section",
            "title": "Add or rename your Experience section",
            "priority": "high",
            "skill": "",
            "evidence": "No recognized Experience section was detected.",
            "action": "Use a standard heading such as Experience or Work Experience. For each role, add dates and 2–4 concise bullets describing your actual work and outcome; do not invent metrics.",
        })
    if not sections.get("education"):
        recommendations.append({
            "type": "section",
            "title": "Add an Education section if applicable",
            "priority": "medium",
            "skill": "",
            "evidence": "No recognized Education section was detected.",
            "action": "Add a standard Education heading with the institution, qualification, and dates only when those details apply to you.",
        })
    if not contact.get("email"):
        recommendations.append({
            "type": "contact",
            "title": "Add a contact email",
            "priority": "high",
            "skill": "",
            "evidence": "No email address was detected in the resume text.",
            "action": "Place a professional email address near your name at the top of the resume and check that it is selectable text in the exported PDF.",
        })
    for phrase in weak_phrases:
        recommendations.append({
            "type": "writing",
            "title": f"Rewrite the phrase “{phrase}”",
            "priority": "low",
            "skill": "",
            "evidence": phrase,
            "action": "Replace the vague wording with the specific action you took and the deliverable you created. Keep the facts and metrics exactly as they occurred.",
        })
    return recommendations