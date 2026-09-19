import re

SECTION_ALIASES = {
    "contact": ["contact", "contact details", "personal info", "profile"],
    "summary": ["summary", "professional summary", "profile summary", "about"],
    "objective": ["objective", "career objective"],
    "skills": ["skills", "technical skills", "core competencies", "competencies"],
    "education": ["education", "academic background", "education history"],
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "projects": ["projects", "selected projects", "project work"],
    "certifications": ["certifications", "licenses", "courses"],
    "achievements": ["achievements", "awards", "highlights"],
    "publications": ["publications", "papers"],
    "languages": ["languages", "language skills"],
    "interests": ["interests", "hobbies"],
    "references": ["references"],
}


def normalize_heading(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    for section, aliases in SECTION_ALIASES.items():
        if value in aliases or value.replace(" ", "") in [a.replace(" ", "") for a in aliases]:
            return section
    return value


def detect_sections(text: str) -> dict:
    sections = {"contact": [], "summary": [], "objective": [], "skills": [], "education": [], "experience": [], "projects": [], "certifications": [], "achievements": [], "publications": [], "languages": [], "interests": [], "references": []}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current = None
    for line in lines:
        heading = normalize_heading(line)
        if heading in sections:
            current = heading
            continue
        if current:
            sections[current].append(line)
    return {k: v for k, v in sections.items() if v}
