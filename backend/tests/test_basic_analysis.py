from app.services.text_cleaner import normalize_whitespace
from app.services.section_detector import detect_sections
from app.services.skill_extractor import extract_skills
from app.services.job_matcher import compute_similarity
from app.services.ats_scorer import calculate_compatibility


def test_normalize_whitespace_keeps_content():
    text = "  Python   developer  with SQL  \\n  and FastAPI    "
    cleaned = normalize_whitespace(text)
    assert "Python developer" in cleaned
    assert "FastAPI" in cleaned


def test_section_detection_finds_skills_and_experience():
    text = "SKILLS\nPython, SQL, FastAPI\nEXPERIENCE\nBackend Engineer at Acme"
    sections = detect_sections(text)
    assert "skills" in sections
    assert "experience" in sections


def test_skill_extraction_detects_known_terms():
    text = "Python, SQL, React, Docker, AWS, PostgreSQL"
    skills = extract_skills(text)
    assert any(item["skill"] == "Python" for item in skills)
    assert any(item["skill"] == "SQL" for item in skills)


def test_similarity_and_scoring_are_numeric():
    resume_text = "Python backend engineer with FastAPI and SQL experience"
    job_text = "Python backend engineer with FastAPI, SQL, Docker"
    similarity = compute_similarity(resume_text, job_text)
    score = calculate_compatibility(similarity, {"matched_skills": ["Python", "FastAPI", "SQL"], "missing_skills": ["Docker"]})
    assert 0 <= similarity <= 1
    assert 0 <= score <= 100
