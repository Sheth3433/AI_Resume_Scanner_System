import re

from app.services.section_detector import detect_sections

SKILL_LIBRARY = {
    "python": {"skill": "Python", "category": "Programming Language"},
    "go programming": {"skill": "Go", "category": "Programming Language"},
    "go language": {"skill": "Go", "category": "Programming Language"},
    "c++": {"skill": "C++", "category": "Programming Language"},
    "c#": {"skill": "C#", "category": "Programming Language"},
    "sql": {"skill": "SQL", "category": "Database"},
    "postgresql": {"skill": "PostgreSQL", "category": "Database"},
    "mysql": {"skill": "MySQL", "category": "Database"},
    "mongo db": {"skill": "MongoDB", "category": "Database"},
    "mongo": {"skill": "MongoDB", "category": "Database"},
    "mongodb": {"skill": "MongoDB", "category": "Database"},
    "sqlite": {"skill": "SQLite", "category": "Database"},
    "redis": {"skill": "Redis", "category": "Database"},
    "oracle": {"skill": "Oracle", "category": "Database"},
    "dynamodb": {"skill": "DynamoDB", "category": "Database"},
    "firebase": {"skill": "Firebase", "category": "Database / Cloud"},
    "java": {"skill": "Java", "category": "Programming Language"},
    "javascript": {"skill": "JavaScript", "category": "Programming Language"},
    "js": {"skill": "JavaScript", "category": "Programming Language"},
    "typescript": {"skill": "TypeScript", "category": "Programming Language"},
    "kotlin": {"skill": "Kotlin", "category": "Programming Language"},
    "swift": {"skill": "Swift", "category": "Programming Language"},
    "rust": {"skill": "Rust", "category": "Programming Language"},
    "php": {"skill": "PHP", "category": "Programming Language"},
    "ruby": {"skill": "Ruby", "category": "Programming Language"},
    "golang": {"skill": "Go", "category": "Programming Language"},
    "go": {"skill": "Go", "category": "Programming Language"},
    "react": {"skill": "React", "category": "Framework"},
    "reactjs": {"skill": "React", "category": "Framework"},
    "node": {"skill": "Node.js", "category": "Framework"},
    "nodejs": {"skill": "Node.js", "category": "Framework"},
    "node.js": {"skill": "Node.js", "category": "Framework"},
    "fastapi": {"skill": "FastAPI", "category": "Framework"},
    "flask": {"skill": "Flask", "category": "Framework"},
    "django": {"skill": "Django", "category": "Framework"},
    "express.js": {"skill": "Express.js", "category": "Framework"},
    "express": {"skill": "Express.js", "category": "Framework"},
    "next.js": {"skill": "Next.js", "category": "Framework"},
    "nextjs": {"skill": "Next.js", "category": "Framework"},
    "angular": {"skill": "Angular", "category": "Framework"},
    "vue.js": {"skill": "Vue.js", "category": "Framework"},
    "vuejs": {"skill": "Vue.js", "category": "Framework"},
    "flutter": {"skill": "Flutter", "category": "Framework"},
    "spring boot": {"skill": "Spring Boot", "category": "Framework"},
    ".net": {"skill": ".NET", "category": "Framework"},
    "docker": {"skill": "Docker", "category": "DevOps"},
    "kubernetes": {"skill": "Kubernetes", "category": "DevOps"},
    "jenkins": {"skill": "Jenkins", "category": "DevOps"},
    "github actions": {"skill": "GitHub Actions", "category": "DevOps"},
    "ci/cd": {"skill": "CI/CD", "category": "DevOps"},
    "aws": {"skill": "AWS", "category": "Cloud"},
    "azure": {"skill": "Azure", "category": "Cloud"},
    "gcp": {"skill": "Google Cloud", "category": "Cloud"},
    "google cloud": {"skill": "Google Cloud", "category": "Cloud"},
    "google cloud platform": {"skill": "Google Cloud", "category": "Cloud"},
    "git": {"skill": "Git", "category": "Tool"},
    "github": {"skill": "GitHub", "category": "Tool"},
    "tableau": {"skill": "Tableau", "category": "Data Science"},
    "power bi": {"skill": "Power BI", "category": "Data Science"},
    "powerbi": {"skill": "Power BI", "category": "Data Science"},
    "pytorch": {"skill": "PyTorch", "category": "AI/ML"},
    "tensorflow": {"skill": "TensorFlow", "category": "AI/ML"},
    "keras": {"skill": "Keras", "category": "AI/ML"},
    "opencv": {"skill": "OpenCV", "category": "AI/ML"},
    "langchain": {"skill": "LangChain", "category": "AI/ML"},
    "hugging face": {"skill": "Hugging Face", "category": "AI/ML"},
    "huggingface": {"skill": "Hugging Face", "category": "AI/ML"},
    "scikit": {"skill": "scikit-learn", "category": "AI/ML"},
    "scikit-learn": {"skill": "scikit-learn", "category": "AI/ML"},
    "pandas": {"skill": "Pandas", "category": "Data Science"},
    "numpy": {"skill": "NumPy", "category": "Data Science"},
    "spark": {"skill": "Apache Spark", "category": "Data Science"},
    "tableau": {"skill": "Tableau", "category": "Data Science"},
    "powerbi": {"skill": "Power BI", "category": "Data Science"},
    "css": {"skill": "CSS", "category": "Web Development"},
    "html": {"skill": "HTML", "category": "Web Development"},
    "tailwind css": {"skill": "Tailwind CSS", "category": "Framework"},
    "bootstrap": {"skill": "Bootstrap", "category": "Framework"},
    "rest": {"skill": "REST APIs", "category": "Web Development"},
    "rest api": {"skill": "REST APIs", "category": "Web Development"},
    "rest apis": {"skill": "REST APIs", "category": "Web Development"},
    "graphql": {"skill": "GraphQL", "category": "Web Development"},
    "grpc": {"skill": "gRPC", "category": "Web Development"},
    "api": {"skill": "APIs", "category": "Web Development"},
    "linux": {"skill": "Linux", "category": "DevOps"},
    "kubernetes": {"skill": "Kubernetes", "category": "DevOps"},
    "terraform": {"skill": "Terraform", "category": "DevOps"},
    "bash": {"skill": "Bash", "category": "DevOps"},
    "powershell": {"skill": "PowerShell", "category": "DevOps"},
    "ci cd": {"skill": "CI/CD", "category": "DevOps"},
    "maven": {"skill": "Maven", "category": "Tool"},
    "gradle": {"skill": "Gradle", "category": "Tool"},
    "junit": {"skill": "JUnit", "category": "Testing"},
    "pytest": {"skill": "pytest", "category": "Testing"},
    "selenium": {"skill": "Selenium", "category": "Testing"},
    "playwright": {"skill": "Playwright", "category": "Testing"},
    "cypress": {"skill": "Cypress", "category": "Testing"},
    "postman": {"skill": "Postman", "category": "Testing"},
    "excel": {"skill": "Excel", "category": "Data Science"},
    "r programming": {"skill": "R", "category": "Programming Language"},
    "wireshark": {"skill": "Wireshark", "category": "Cybersecurity"},
    "owasp": {"skill": "OWASP", "category": "Cybersecurity"},
    "burp suite": {"skill": "Burp Suite", "category": "Cybersecurity"},
    "nmap": {"skill": "Nmap", "category": "Cybersecurity"},
    "metasploit": {"skill": "Metasploit", "category": "Cybersecurity"},
    "siem": {"skill": "SIEM", "category": "Cybersecurity"},
    "incident response": {"skill": "Incident Response", "category": "Cybersecurity"},
    "risk assessment": {"skill": "Risk Assessment", "category": "Cybersecurity"},
    "cloudformation": {"skill": "CloudFormation", "category": "Cloud"},
    "microservices": {"skill": "Microservices", "category": "Architecture"},
    "kafka": {"skill": "Kafka", "category": "Data Engineering"},
    "rabbitmq": {"skill": "RabbitMQ", "category": "Data Engineering"},
    "networking": {"skill": "Networking", "category": "Networking"},
    "presentation": {"skill": "Presentation", "category": "Soft Skill"},
    "communication": {"skill": "Communication", "category": "Soft Skill"},
    "leadership": {"skill": "Leadership", "category": "Soft Skill"},
    "teamwork": {"skill": "Teamwork", "category": "Soft Skill"},
}


def normalize_skill_name(value: str) -> str:
    key = value.strip().lower().replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", key).strip()


def _skill_pattern(alias: str) -> re.Pattern:
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


def _line_at(text: str, position: int) -> str:
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    return text[start:] if end == -1 else text[start:end]


def _is_negated(line: str, position: int) -> bool:
    prefix = line[:position].casefold()
    if re.search(r"\bnot\s+(?:only|just)\b", prefix):
        return False
    return bool(re.search(
        r"\b(?:not|no|never|without|lack(?:s|ed|ing)?|don't|doesn't|didn't|isn't|aren't)\b(?:\W+\w+){0,4}\W*$",
        prefix,
    ))


def extract_skills(text: str):
    sections = detect_sections(text)
    section_by_line = {
        line: section
        for section, lines in sections.items()
        for line in lines
    }
    results = {}
    aliases = sorted(SKILL_LIBRARY, key=len, reverse=True)
    for alias in aliases:
        item = SKILL_LIBRARY[alias]
        for match in _skill_pattern(alias).finditer(text):
            line = _line_at(text, match.start()).strip()
            line_position = match.start() - (text.rfind("\n", 0, match.start()) + 1)
            if alias == "go" and not (
                section_by_line.get(line) == "skills"
                or re.search(r"\b(?:golang|go\s+(?:programming|language))\b", line, re.I)
                or re.search(r"(?:^|[,/|])\s*go\s*(?:[,/|]|$)", line, re.I)
            ):
                continue
            if _is_negated(line, line_position):
                continue
            section = section_by_line.get(line)
            confidence = 0.95 if section == "skills" else 0.85 if section in {"experience", "projects"} else 0.7 if section else 0.65
            canonical = item["skill"]
            candidate = {
                "skill": canonical,
                "category": item["category"],
                "evidence": line,
                "confidence": confidence,
                "source_section": section or "not_detected",
            }
            current = results.get(canonical)
            if current is None or candidate["confidence"] > current["confidence"]:
                results[canonical] = candidate
    return sorted(results.values(), key=lambda item: item["skill"].casefold())


def classify_job_skills(text: str, skills: list[dict]) -> list[dict]:
    lines = text.splitlines()
    required_terms = re.compile(r"\b(required|must[- ]have|mandatory|essential|minimum qualification)\b", re.I)
    preferred_terms = re.compile(r"\b(preferred|nice[- ]to[- ]have|bonus|desirable|a plus)\b", re.I)
    neutralize_required = re.compile(r"\b(not required|not mandatory|not essential|optional)\b", re.I)
    heading = re.compile(r"\b(required|requirements|must[- ]have|preferred|qualifications)\b", re.I)
    classified = []

    for skill in skills:
        aliases = [alias for alias, item in SKILL_LIBRARY.items() if item["skill"] == skill["skill"]]
        mentions = [match for alias in aliases for match in _skill_pattern(alias).finditer(text)]
        contexts = []
        for mention in mentions:
            line_start = text.rfind("\n", 0, mention.start()) + 1
            line_index = text.count("\n", 0, mention.start())
            context = _line_at(text, mention.start())
            sentence_start = max(context.rfind(mark, 0, mention.start() - line_start) for mark in ".!?;") + 1
            sentence_endings = [context.find(mark, mention.end() - line_start) for mark in ".!?;" if context.find(mark, mention.end() - line_start) >= 0]
            sentence_end = min(sentence_endings) if sentence_endings else len(context)
            local_context = context[sentence_start:sentence_end]
            if neutralize_required.search(local_context):
                priority = "mentioned"
            elif preferred_terms.search(local_context):
                priority = "preferred"
            elif required_terms.search(local_context):
                priority = "required"
            else:
                prior_heading = next((
                    candidate
                    for candidate in reversed(lines[max(0, line_index - 4):line_index])
                    if candidate.strip() and heading.search(candidate)
                ), "")
                if prior_heading and re.search(r"required|requirements|must[- ]have", prior_heading, re.I):
                    priority = "required"
                elif prior_heading and re.search(r"preferred|nice[- ]to[- ]have|desirable", prior_heading, re.I):
                    priority = "preferred"
                else:
                    priority = "mentioned"
            contexts.append((priority, local_context.strip()))
        if any(priority == "required" for priority, _ in contexts):
            importance = "required"
        elif any(priority == "preferred" for priority, _ in contexts):
            importance = "preferred"
        else:
            importance = "mentioned"
        evidence = next((context for priority, context in contexts if priority == importance and context), skill.get("evidence", ""))
        classified.append({**skill, "importance": importance, "evidence": evidence})
    return classified
