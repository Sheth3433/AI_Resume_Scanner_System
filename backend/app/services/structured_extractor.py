from __future__ import annotations

import re

from app.services.skill_extractor import extract_skills


NOT_DETECTED = "Not detected"
DATE_PATTERN = re.compile(
    r"\b(?P<start>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?\s+)?(?:19|20)\d{2})"
    r"\s*(?:-|\u2013|\u2014|to)\s*"
    r"(?P<end>(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?\s+)?(?:19|20)\d{2}|Present|Current))\b",
    re.I,
)
DEGREE_PATTERN = re.compile(r"\b(?:bachelor(?:'s)?|master(?:'s)?|b\.?\s?tech|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|b\.?\s?e|m\.?\s?e|ph\.?d|diploma|associate)\b", re.I)
RESULT_PATTERN = re.compile(r"\b(?:CGPA|GPA|percentage|score)\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?\s*%?)", re.I)
FULL_DEGREE_PATTERN = re.compile(r"\b(?:bachelor(?:'s)?(?:\s+of\s+[\w&]+(?:\s+[\w&]+)?)?|master(?:'s)?(?:\s+of\s+[\w&]+(?:\s+[\w&]+)?)?|b\.?\s?tech|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|b\.?\s?e|m\.?\s?e|ph\.?d|diploma|associate(?:'s)?)\b", re.I)


def _clean_line(line: str) -> str:
    return re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", line).strip()


def _date_range(line: str) -> tuple[str, str]:
    match = DATE_PATTERN.search(line)
    if not match:
        return NOT_DETECTED, NOT_DETECTED
    return match.group("start"), match.group("end")


def extract_experience_records(lines: list[str]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for original in lines:
        line = _clean_line(original)
        if not line:
            continue
        start, end = _date_range(line)
        starts_record = start != NOT_DETECTED or (current is None and re.search(r"\s+at\s+", line, re.I))
        if starts_record:
            if current:
                records.append(current)
            header = DATE_PATTERN.sub("", line).strip(" |,-\u2013\u2014")
            role = NOT_DETECTED
            company = NOT_DETECTED
            at_match = re.search(r"(?P<role>.+?)\s+at\s+(?P<company>.+)", header, re.I)
            if at_match:
                role = at_match.group("role").strip(" |,-") or NOT_DETECTED
                company = at_match.group("company").strip(" |,-") or NOT_DETECTED
            else:
                parts = [part.strip() for part in re.split(r"\s*[|,]\s*", header) if part.strip()]
                if parts:
                    role = parts[0]
                if len(parts) > 1:
                    company = parts[1]
            current = {
                "role": role,
                "company": company,
                "start_date": start,
                "end_date": end,
                "description": NOT_DETECTED,
                "evidence": line,
            }
        elif current:
            current["description"] = line if current["description"] == NOT_DETECTED else f"{current['description']} {line}"
            current["evidence"] = f"{current['evidence']}\n{line}"
        else:
            records.append({
                "role": NOT_DETECTED,
                "company": NOT_DETECTED,
                "start_date": NOT_DETECTED,
                "end_date": NOT_DETECTED,
                "description": line,
                "evidence": line,
            })
    if current:
        records.append(current)
    return records


def extract_education_records(lines: list[str]) -> list[dict[str, str]]:
    records = []
    for original in lines:
        line = _clean_line(original)
        if not line:
            continue
        degree_match = DEGREE_PATTERN.search(line)
        full_degree_match = FULL_DEGREE_PATTERN.search(line)
        result_match = RESULT_PATTERN.search(line)
        year_matches = re.findall(r"\b(?:19|20)\d{2}\b", line)
        year_match = year_matches[-1] if year_matches else None
        parts = [part.strip() for part in re.split(r"\s*[|,]\s*", line) if part.strip()]
        institution = NOT_DETECTED
        if len(parts) > 1:
            institution = DATE_PATTERN.sub("", parts[1]).strip(" -") or NOT_DETECTED
        field_match = re.search(r"\b(?:in|major(?:ing)?\s+in)\s+([^|,;]+)", line, re.I)
        field = field_match.group(1).strip(" -") if field_match else NOT_DETECTED
        if field != NOT_DETECTED:
            field = re.sub(r"\b(?:19|20)\d{2}\b.*$", "", field).strip(" -") or NOT_DETECTED
        degree = full_degree_match.group(0) if full_degree_match else degree_match.group(0) if degree_match else NOT_DETECTED
        if degree != NOT_DETECTED:
            degree = re.sub(r"\s+in$", "", degree, flags=re.I)
        records.append({
            "degree": degree,
            "institution": institution,
            "field": field,
            "graduation_year": year_match if year_match else NOT_DETECTED,
            "result": result_match.group(1) if result_match else NOT_DETECTED,
            "evidence": line,
        })
    return records


def extract_project_records(lines: list[str]) -> list[dict[str, str | list[str]]]:
    records = []
    for original in lines:
        line = _clean_line(original)
        if not line:
            continue
        delimiter = re.search(r"\s*[:|\u2013\u2014]\s*", line)
        title = line[:delimiter.start()].strip() if delimiter and delimiter.start() > 0 else NOT_DETECTED
        description = line[delimiter.end():].strip() if delimiter else line
        link_match = re.search(r"https?://\S+", line, re.I)
        records.append({
            "project_name": title or NOT_DETECTED,
            "technologies": [item["skill"] for item in extract_skills(line)],
            "description": description or NOT_DETECTED,
            "link": link_match.group(0).rstrip(".,)") if link_match else NOT_DETECTED,
            "evidence": line,
        })
    return records


def extract_certification_records(lines: list[str]) -> list[dict[str, str]]:
    records = []
    for original in lines:
        line = _clean_line(original)
        if line:
            parts = [part.strip() for part in re.split(r"\s*[|,]\s*", line) if part.strip()]
            years = re.findall(r"\b(?:19|20)\d{2}\b", line)
            records.append({
                "certification": parts[0],
                "issuer": parts[1] if len(parts) > 1 else NOT_DETECTED,
                "date": years[-1] if years else NOT_DETECTED,
                "evidence": line,
            })
    return records


def extract_structured_resume(sections: dict[str, list[str]]) -> dict[str, list[dict]]:
    return {
        "education": extract_education_records(sections.get("education", [])),
        "experience": extract_experience_records(sections.get("experience", [])),
        "projects": extract_project_records(sections.get("projects", [])),
        "certifications": extract_certification_records(sections.get("certifications", [])),
    }