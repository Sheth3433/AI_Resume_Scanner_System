import re

SKILL_LIBRARY = {
    "python": {"skill": "Python", "category": "Programming Language"},
    "sql": {"skill": "SQL", "category": "Database"},
    "postgresql": {"skill": "PostgreSQL", "category": "Database"},
    "mysql": {"skill": "MySQL", "category": "Database"},
    "mongo": {"skill": "MongoDB", "category": "Database"},
    "mongodb": {"skill": "MongoDB", "category": "Database"},
    "java": {"skill": "Java", "category": "Programming Language"},
    "javascript": {"skill": "JavaScript", "category": "Programming Language"},
    "js": {"skill": "JavaScript", "category": "Programming Language"},
    "typescript": {"skill": "TypeScript", "category": "Programming Language"},
    "react": {"skill": "React", "category": "Framework"},
    "reactjs": {"skill": "React", "category": "Framework"},
    "node": {"skill": "Node.js", "category": "Framework"},
    "nodejs": {"skill": "Node.js", "category": "Framework"},
    "fastapi": {"skill": "FastAPI", "category": "Framework"},
    "flask": {"skill": "Flask", "category": "Framework"},
    "django": {"skill": "Django", "category": "Framework"},
    "docker": {"skill": "Docker", "category": "DevOps"},
    "aws": {"skill": "AWS", "category": "Cloud"},
    "azure": {"skill": "Azure", "category": "Cloud"},
    "gcp": {"skill": "Google Cloud", "category": "Cloud"},
    "git": {"skill": "Git", "category": "Tool"},
    "github": {"skill": "GitHub", "category": "Tool"},
    "pytorch": {"skill": "PyTorch", "category": "AI/ML"},
    "tensorflow": {"skill": "TensorFlow", "category": "AI/ML"},
    "keras": {"skill": "Keras", "category": "AI/ML"},
    "scikit": {"skill": "scikit-learn", "category": "AI/ML"},
    "scikit-learn": {"skill": "scikit-learn", "category": "AI/ML"},
    "pandas": {"skill": "Pandas", "category": "Data Science"},
    "numpy": {"skill": "NumPy", "category": "Data Science"},
    "spark": {"skill": "Apache Spark", "category": "Data Science"},
    "tableau": {"skill": "Tableau", "category": "Data Science"},
    "powerbi": {"skill": "Power BI", "category": "Data Science"},
    "css": {"skill": "CSS", "category": "Web Development"},
    "html": {"skill": "HTML", "category": "Web Development"},
    "rest": {"skill": "REST APIs", "category": "Web Development"},
    "api": {"skill": "APIs", "category": "Web Development"},
    "linux": {"skill": "Linux", "category": "DevOps"},
    "kubernetes": {"skill": "Kubernetes", "category": "DevOps"},
    "terraform": {"skill": "Terraform", "category": "DevOps"},
    "communication": {"skill": "Communication", "category": "Soft Skill"},
    "leadership": {"skill": "Leadership", "category": "Soft Skill"},
    "teamwork": {"skill": "Teamwork", "category": "Soft Skill"},
}


def normalize_skill_name(value: str) -> str:
    key = value.strip().lower().replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", key).strip()


def extract_skills(text: str):
    results = []
    seen = set()
    normalized_text = text.lower()
    for key, item in SKILL_LIBRARY.items():
        pattern = rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])"
        match = re.search(pattern, normalized_text)
        if match:
            skill = item["skill"]
            if skill not in seen:
                seen.add(skill)
                results.append({
                    "skill": skill,
                    "category": item["category"],
                    "evidence": text[match.start():match.end()],
                    "confidence": 0.9,
                })
    return results
