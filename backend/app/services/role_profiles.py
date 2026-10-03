from __future__ import annotations

from app.services.skill_extractor import extract_skills


ROLE_PROFILES: dict[str, dict] = {
    "Backend Developer": {
        "description": "Build server-side applications, APIs, databases, and backend services.",
        "skill_groups": [
            {"group": "Programming language", "skills": ["Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C#", "PHP", "Ruby", "Kotlin"], "weight": 25},
            {"group": "Backend framework", "skills": ["FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "Express.js", ".NET"], "weight": 25},
            {"group": "API development", "skills": ["APIs", "REST APIs", "GraphQL", "gRPC"], "weight": 25},
            {"group": "Database", "skills": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB"], "weight": 25},
        ],
        "optional_alternatives": [
            {"label": "Other backend language options (not all required)", "skills": ["Node.js", "Go", "Rust", "Java"]},
            {"label": "Common supporting skills", "skills": ["Docker", "AWS", "Linux", "Git", "CI/CD"]},
        ],
    },
    "Frontend Developer": {
        "description": "Build accessible, responsive user interfaces for web applications.",
        "skill_groups": [
            {"group": "Web language", "skills": ["JavaScript", "TypeScript"], "weight": 35},
            {"group": "UI framework", "skills": ["React", "Angular", "Vue.js"], "weight": 35},
            {"group": "Browser fundamentals", "skills": ["HTML", "CSS"], "weight": 20},
            {"group": "Frontend tooling", "skills": ["Git", "Tailwind CSS", "Bootstrap"], "weight": 10},
        ],
        "optional_alternatives": [{"label": "Other UI frameworks (alternatives)", "skills": ["React", "Angular", "Vue.js"]}],
    },
    "Full Stack Developer": {
        "description": "Deliver frontend and backend features across a web application stack.",
        "skill_groups": [
            {"group": "Web language", "skills": ["JavaScript", "TypeScript"], "weight": 25},
            {"group": "Frontend framework", "skills": ["React", "Angular", "Vue.js"], "weight": 25},
            {"group": "Backend framework", "skills": ["Node.js", "Express.js", "FastAPI", "Django", "Flask", "Spring Boot"], "weight": 25},
            {"group": "API and database", "skills": ["APIs", "REST APIs", "GraphQL", "SQL", "PostgreSQL", "MongoDB"], "weight": 25},
        ],
        "optional_alternatives": [{"label": "Other full-stack technologies (alternatives)", "skills": ["Python", "Java", "Go", "Docker", "AWS"]}],
    },
    "Python Developer": {
        "description": "Build software, automation, APIs, or data applications using Python.",
        "skill_groups": [
            {"group": "Language", "skills": ["Python"], "weight": 35},
            {"group": "Python framework", "skills": ["FastAPI", "Django", "Flask"], "weight": 25},
            {"group": "Data or persistence", "skills": ["SQL", "PostgreSQL", "MongoDB", "Pandas", "NumPy"], "weight": 20},
            {"group": "Version control", "skills": ["Git", "GitHub"], "weight": 10},
            {"group": "Testing", "skills": ["pytest"], "weight": 10},
        ],
        "optional_alternatives": [{"label": "Common supporting skills", "skills": ["Docker", "AWS", "Linux", "REST APIs"]}],
    },
    "Java Developer": {
        "description": "Build Java applications, services, and enterprise backends.",
        "skill_groups": [
            {"group": "Language", "skills": ["Java"], "weight": 35},
            {"group": "Java framework", "skills": ["Spring Boot"], "weight": 25},
            {"group": "API and database", "skills": ["REST APIs", "SQL", "PostgreSQL", "MySQL", "Oracle"], "weight": 25},
            {"group": "Build and version control", "skills": ["Maven", "Gradle", "Git"], "weight": 15},
        ],
        "optional_alternatives": [{"label": "Common supporting skills", "skills": ["Docker", "AWS", "JUnit"]}],
    },
    "Data Analyst": {
        "description": "Query, clean, analyze, and communicate business or product data.",
        "skill_groups": [
            {"group": "Query language", "skills": ["SQL"], "weight": 35},
            {"group": "Data analysis tools", "skills": ["Excel", "Tableau", "Power BI"], "weight": 30},
            {"group": "Data manipulation", "skills": ["Pandas", "NumPy", "Python"], "weight": 25},
            {"group": "Data communication", "skills": ["Communication", "Presentation"], "weight": 10},
        ],
        "optional_alternatives": [{"label": "Other visualization tools (alternatives)", "skills": ["Tableau", "Power BI"]}],
    },
    "Data Scientist": {
        "description": "Use statistics, programming, and machine learning to analyze data.",
        "skill_groups": [
            {"group": "Programming", "skills": ["Python", "R"], "weight": 25},
            {"group": "Data manipulation", "skills": ["Pandas", "NumPy", "Apache Spark"], "weight": 25},
            {"group": "Machine learning", "skills": ["scikit-learn", "TensorFlow", "PyTorch"], "weight": 30},
            {"group": "Data querying", "skills": ["SQL", "PostgreSQL"], "weight": 20},
        ],
        "optional_alternatives": [{"label": "Other model frameworks (alternatives)", "skills": ["TensorFlow", "PyTorch", "scikit-learn"]}],
    },
    "AI/ML Engineer": {
        "description": "Develop, evaluate, and deploy machine learning or AI systems.",
        "skill_groups": [
            {"group": "Programming", "skills": ["Python"], "weight": 25},
            {"group": "ML framework", "skills": ["PyTorch", "TensorFlow", "Keras", "scikit-learn"], "weight": 30},
            {"group": "Model/data tooling", "skills": ["Hugging Face", "LangChain", "OpenCV", "Pandas", "NumPy"], "weight": 25},
            {"group": "Serving and APIs", "skills": ["FastAPI", "REST APIs", "Docker"], "weight": 20},
        ],
        "optional_alternatives": [{"label": "Other ML frameworks (alternatives)", "skills": ["PyTorch", "TensorFlow", "Keras"]}],
    },
    "DevOps Engineer": {
        "description": "Automate delivery, infrastructure, deployment, and service reliability.",
        "skill_groups": [
            {"group": "Containers", "skills": ["Docker", "Kubernetes"], "weight": 25},
            {"group": "Cloud platform", "skills": ["AWS", "Azure", "Google Cloud"], "weight": 25},
            {"group": "Infrastructure automation", "skills": ["Terraform", "Jenkins", "GitHub Actions", "CI/CD"], "weight": 25},
            {"group": "Systems and scripting", "skills": ["Linux", "Python", "Bash"], "weight": 25},
        ],
        "optional_alternatives": [{"label": "Cloud platforms (alternatives)", "skills": ["AWS", "Azure", "Google Cloud"]}],
    },
    "Mobile Developer": {
        "description": "Build and maintain mobile applications for Android or iOS.",
        "skill_groups": [
            {"group": "Mobile framework", "skills": ["Flutter", "React Native"], "weight": 35},
            {"group": "Native language", "skills": ["Kotlin", "Java", "Swift"], "weight": 35},
            {"group": "Mobile data/API integration", "skills": ["Firebase", "REST APIs", "GraphQL"], "weight": 20},
            {"group": "Version control", "skills": ["Git", "GitHub"], "weight": 10},
        ],
        "optional_alternatives": [{"label": "Other mobile approaches (alternatives)", "skills": ["Flutter", "React Native", "Kotlin", "Swift"]}],
    },
    "QA Automation Engineer": {
        "description": "Design test strategies and automate quality checks for software.",
        "skill_groups": [
            {"group": "Automation language", "skills": ["Python", "Java", "JavaScript", "TypeScript"], "weight": 25},
            {"group": "Test automation", "skills": ["Selenium", "Playwright", "Cypress", "pytest", "JUnit"], "weight": 35},
            {"group": "API and test tooling", "skills": ["Postman", "REST APIs", "Git"], "weight": 25},
            {"group": "Delivery workflow", "skills": ["CI/CD", "GitHub Actions", "Jenkins"], "weight": 15},
        ],
        "optional_alternatives": [{"label": "Automation frameworks (alternatives)", "skills": ["Selenium", "Playwright", "Cypress"]}],
    },
    "Cybersecurity Analyst": {
        "description": "Monitor, investigate, and reduce security risks in systems and networks.",
        "skill_groups": [
            {"group": "Operating systems and networks", "skills": ["Linux", "Networking", "Wireshark"], "weight": 25},
            {"group": "Security testing/tools", "skills": ["OWASP", "Burp Suite", "Nmap", "Metasploit"], "weight": 30},
            {"group": "Scripting or automation", "skills": ["Python", "Bash", "PowerShell"], "weight": 20},
            {"group": "Security operations", "skills": ["SIEM", "Incident Response", "Risk Assessment"], "weight": 25},
        ],
        "optional_alternatives": [{"label": "Common security tools (alternatives)", "skills": ["Wireshark", "Burp Suite", "Nmap"]}],
    },
    "Cloud Engineer": {
        "description": "Design and operate secure, scalable cloud infrastructure and services.",
        "skill_groups": [
            {"group": "Cloud platform", "skills": ["AWS", "Azure", "Google Cloud"], "weight": 30},
            {"group": "Infrastructure as code", "skills": ["Terraform", "CloudFormation"], "weight": 25},
            {"group": "Containers and orchestration", "skills": ["Docker", "Kubernetes"], "weight": 25},
            {"group": "Systems and automation", "skills": ["Linux", "Python", "CI/CD"], "weight": 20},
        ],
        "optional_alternatives": [{"label": "Cloud providers (alternatives)", "skills": ["AWS", "Azure", "Google Cloud"]}],
    },
    "Database Engineer": {
        "description": "Design, tune, secure, and operate database systems.",
        "skill_groups": [
            {"group": "Database query and design", "skills": ["SQL", "PostgreSQL", "MySQL", "Oracle", "MongoDB"], "weight": 40},
            {"group": "Data platforms", "skills": ["Redis", "DynamoDB", "Apache Spark"], "weight": 20},
            {"group": "Programming and automation", "skills": ["Python", "Java", "Bash"], "weight": 20},
            {"group": "Cloud and operations", "skills": ["AWS", "Azure", "Linux", "Docker"], "weight": 20},
        ],
        "optional_alternatives": [{"label": "Database engines (alternatives)", "skills": ["PostgreSQL", "MySQL", "Oracle", "MongoDB"]}],
    },
}


def list_role_profiles() -> list[dict[str, str]]:
    return [{"role": name, "description": profile["description"]} for name, profile in ROLE_PROFILES.items()]


def analyze_role_fit(role: str | None, resume_skill_details: list[dict], sections: dict[str, list[str]]) -> dict | None:
    if not role:
        return None
    profile = ROLE_PROFILES.get(role)
    if profile is None:
        return None

    present = {item["skill"] for item in resume_skill_details}
    groups = []
    required_skills = set()
    for group in profile["skill_groups"]:
        matched = sorted(present.intersection(group["skills"]))
        met = bool(matched)
        required_skills.update(group["skills"])
        evidence = [
            item["evidence"]
            for item in resume_skill_details
            if item["skill"] in matched
        ]
        groups.append({
            "group": group["group"],
            "skills": group["skills"],
            "matched_skills": matched,
            "status": "met" if met else "not_detected",
            "weight": group["weight"],
            "evidence": evidence,
        })

    project_lines = sections.get("projects", [])
    related_projects = []
    for line in project_lines:
        line_skills = {item["skill"] for item in extract_skills(line)}
        project_matches = sorted(line_skills.intersection(required_skills))
        if project_matches:
            related_projects.append({"evidence": line, "matched_skills": project_matches})

    optional_alternatives = []
    for alternative_group in profile["optional_alternatives"]:
        missing = [skill for skill in alternative_group["skills"] if skill not in present]
        if missing:
            optional_alternatives.append({"label": alternative_group["label"], "skills": missing})

    return {
        "role": role,
        "description": profile["description"],
        "required_groups_met": sum(1 for group in groups if group["status"] == "met"),
        "total_required_groups": len(groups),
        "related_project_count": len(related_projects),
        "project_count": len(project_lines),
        "skill_groups": groups,
        "unmet_groups": [group for group in groups if group["status"] == "not_detected"],
        "optional_alternatives": optional_alternatives,
        "related_projects": related_projects,
    }