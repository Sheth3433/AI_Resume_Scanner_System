from __future__ import annotations


ROLE_SKILLS = {
    "Backend Developer": {"Python", "Java", "Node.js", "FastAPI", "Flask", "Django", "Express.js", "SQL", "PostgreSQL", "REST APIs"},
    "Frontend Developer": {"JavaScript", "TypeScript", "React", "Angular", "Vue.js", "HTML", "CSS", "Next.js"},
    "Full Stack Developer": {"JavaScript", "TypeScript", "React", "Node.js", "Express.js", "Python", "FastAPI", "SQL", "HTML", "CSS"},
    "Data Analyst": {"SQL", "Python", "Pandas", "NumPy", "Tableau", "Power BI", "Excel"},
    "Data Scientist": {"Python", "Pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch", "SQL", "Tableau"},
    "AI/ML Engineer": {"Python", "PyTorch", "TensorFlow", "Keras", "scikit-learn", "OpenCV", "Hugging Face", "LangChain", "FastAPI"},
    "DevOps Engineer": {"Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "Terraform", "Linux", "Jenkins", "GitHub Actions", "CI/CD"},
    "Mobile Developer": {"Kotlin", "Swift", "Flutter", "React Native", "Java", "Firebase"},
}


def recommend_roles(resume_skills: list[str]) -> list[dict[str, object]]:
    present = set(resume_skills)
    recommendations = []
    for role, role_skills in ROLE_SKILLS.items():
        matched = sorted(present & role_skills)
        if len(matched) < 2:
            continue
        score = round(len(matched) / len(role_skills) * 100)
        if score < 20:
            continue
        missing = sorted(role_skills - present)
        recommendations.append({
            "role": role,
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing[:5],
            "reason": f"{len(matched)} of {len(role_skills)} role-related skills were detected: {', '.join(matched)}.",
        })
    return sorted(recommendations, key=lambda item: (-int(item["match_score"]), str(item["role"])))[:5]