import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes import resume as resume_routes
from app.models.analysis import AnalysisRecord
from app.models.database import Base
from app.models.user import UserRecord
from app.services.auth_service import create_access_token, decode_access_token, hash_password, verify_password
from app.api.routes import auth as auth_routes
from app.services.document_parser import validate_resume_content
from app.services.text_cleaner import normalize_whitespace
from app.services.section_detector import detect_sections
from app.services.skill_extractor import extract_skills
from app.services.skill_extractor import classify_job_skills
from app.services.job_matcher import compute_similarity
from app.services.ats_scorer import calculate_compatibility
from app.services.ats_scorer import analyze_ats
from app.services.resume_parser import build_resume_summary
from app.services.resume_improvement import improve_resume_text
from app.services.report_generator import generate_analysis_report
from app.services.role_recommender import recommend_roles
from app.services.role_profiles import analyze_role_fit
from app.services.role_profiles import list_role_profiles
from fastapi import HTTPException


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


def test_skill_extraction_normalizes_aliases_and_ignores_negated_mentions():
    skills = extract_skills(
        "SKILLS\nPython, Power BI, Node.js\nNOTES\nDo not use Docker."
    )
    by_name = {item["skill"]: item for item in skills}
    assert {"Python", "Power BI", "Node.js"}.issubset(by_name)
    assert "Docker" not in by_name
    assert "Power BI" in by_name["Power BI"]["evidence"]
    assert by_name["Python"]["source_section"] == "skills"
    assert not any(item["skill"] == "Go" for item in extract_skills("I go to work with Python."))
    assert any(item["skill"] == "Go" for item in extract_skills("SKILLS\nPython, Go"))


def test_job_skill_priority_carries_across_requirement_bullets():
    description = "Required skills:\n- Docker\n- AWS\n\nPreferred:\n- Tableau"
    skills = classify_job_skills(description, extract_skills(description))
    priority_by_skill = {item["skill"]: item["importance"] for item in skills}
    assert priority_by_skill == {"AWS": "required", "Docker": "required", "Tableau": "preferred"}


def test_skill_gap_and_recommendations_are_specific_and_prioritized(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.2, "test"))
    result = build_resume_summary(
        "Alex Example\nalex@example.com\nEXPERIENCE\nBuilt a data API with Python.",
        "Required: Docker. Preferred: AWS. Python experience is required.",
    )
    job_skills = {item["skill"]: item for item in result["job"]["skills"]}
    assert job_skills["Docker"]["importance"] == "required"
    assert job_skills["AWS"]["importance"] == "preferred"
    assert job_skills["Docker"]["evidence"] == "Required: Docker"
    assert job_skills["AWS"]["evidence"] == "Preferred: AWS"
    assert result["scores"]["skill_match"] == 44
    details = result["recommendation_details"]
    docker_gap = next(item for item in details if item["skill"] == "Docker")
    assert docker_gap["priority"] == "high"
    assert "Do not add it unless" in docker_gap["action"]
    assert docker_gap["evidence"]
    python_guidance = next(item for item in details if item.get("skill") == "Python")
    assert "Skills section" in python_guidance["action"]

    skills_only = build_resume_summary(
        "Alex Example\nalex@example.com\nSKILLS\nPython",
        "Python is not required.",
    )
    python_guidance = next(item for item in skills_only["recommendation_details"] if item.get("skill") == "Python")
    assert python_guidance["type"] == "skill_evidence"
    assert "do not invent" in python_guidance["action"].lower()
    assert {item["skill"]: item["importance"] for item in skills_only["job"]["skills"]}["Python"] == "mentioned"


def test_role_recommendations_need_multiple_detected_skills_and_explain_overlap():
    assert recommend_roles(["Python"]) == []
    roles = recommend_roles(["Python", "SQL", "Pandas", "Power BI"])
    analyst = next(role for role in roles if role["role"] == "Data Analyst")
    assert "match_score" not in analyst
    assert {"Python", "SQL", "Pandas", "Power BI"}.issubset(analyst["matched_skills"])
    assert "Power BI" in analyst["reason"]
    assert " of " not in analyst["reason"]


def test_settings_status_never_returns_an_api_key():
    settings = resume_routes.get_settings_status(None)
    assert settings["ai"]["configured"] in {True, False}
    assert "api_key" not in settings["ai"]
    assert "secret" not in settings["ai"]


def test_similarity_and_scoring_are_numeric():
    resume_text = "Python backend engineer with FastAPI and SQL experience"
    job_text = "Python backend engineer with FastAPI, SQL, Docker"
    similarity = compute_similarity(resume_text, job_text)
    score = calculate_compatibility(similarity, {"matched_skills": ["Python", "FastAPI", "SQL"], "missing_skills": ["Docker"]})
    assert 0 <= similarity <= 1
    assert 0 <= score <= 100
    assert compute_similarity("Python Python", "Python Docker") < 0.75
    assert compute_similarity("Python", "Docker") == 0
    assert calculate_compatibility(0.5, {"matched_skills": ["Python", "Docker"], "missing_skills": ["AWS", "Go"]}) == 50.0
    assert calculate_compatibility(-0.5, {"matched_skills": ["Python"], "missing_skills": []}) == 40.0


def test_ats_estimate_explains_checks_and_does_not_claim_layout_detection():
    result = build_resume_summary(
        "Alex Example\nalex@example.com\n555-123-4567\nSKILLS\nPython\nEXPERIENCE\nBuilt APIs",
        "Python developer",
    )
    ats = result["ats_analysis"]
    assert 0 <= ats["score"] <= 100
    assert any(check["name"] == "Job-specific skills" for check in ats["checks"])
    assert "Not assessed" in ats["formatting_assessment"]
    assert "proprietary" in ats["disclaimer"]


def test_ats_score_uses_semantic_60_and_exact_skill_coverage_40(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.5, "sentence-transformers"))
    result = build_resume_summary(
        "Alex Example\nSKILLS\nDocker",
        "Required: Docker\nPreferred: AWS",
    )
    assert result["scores"]["skill_match"] == 80
    assert result["scores"]["ats_compatibility"] == 62.0
    assert result["ats_analysis"]["formula"] == "60% semantic similarity + 40% weighted exact skill coverage"

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.5, "test"))
    unknown_terms = build_resume_summary("Alex Example", "Distributed systems specialist")
    assert unknown_terms["job"]["skills"] == []
    assert unknown_terms["scores"]["skill_match"] == 100
    assert unknown_terms["scores"]["ats_compatibility"] == 70
    assert "No skills from the current IT taxonomy" in next(
        check["detail"] for check in unknown_terms["ats_analysis"]["checks"] if check["name"] == "Job-specific skills"
    )


def test_unknown_target_role_is_rejected():
    try:
        build_resume_summary("Python developer", target_role="Chief Wizard")
    except ValueError as error:
        assert "Unsupported IT target role" in str(error)
    else:
        raise AssertionError("Unknown target role was silently accepted")


def test_role_profile_matches_alternative_languages_and_uses_project_evidence(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.4, "test"))
    result = build_resume_summary(
        "Alex Example\nSKILLS\nPython, Java\nPROJECTS\nAPI service built with Python and FastAPI using PostgreSQL.",
        target_role="Backend Developer",
    )
    role_fit = result["role_analysis"]
    assert role_fit["role"] == "Backend Developer"
    language_group = next(group for group in role_fit["skill_groups"] if group["group"] == "Programming language")
    assert language_group["status"] == "met"
    assert "Python" in language_group["matched_skills"]
    assert any("Node.js" in item["skills"] and "Go" in item["skills"] and "Rust" in item["skills"] for item in role_fit["optional_alternatives"])
    api_group = next(group for group in role_fit["skill_groups"] if group["group"] == "API development")
    assert api_group["status"] == "met"
    assert role_fit["required_groups_met"] == 4
    assert role_fit["total_required_groups"] == 4
    assert role_fit["related_project_count"] == 1
    assert role_fit["project_count"] == 1
    assert any("FastAPI" in project["matched_skills"] for project in result["resume"]["projects"])


def test_job_description_and_selected_role_both_contribute_to_skill_match(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.5, "test"))
    result = build_resume_summary(
        "Alex Example\nSKILLS\nPython, FastAPI, APIs\nPROJECTS\nService API: Built with Python and FastAPI.",
        "Required: Docker",
        target_role="Backend Developer",
    )
    assert result["skill_match_basis"]["job_description"] == 0
    assert result["skill_match_basis"]["role_profile"] == 75
    assert result["skill_match_basis"]["combined_weights"] == {"job_description": 60, "role_profile": 40}
    assert result["scores"]["skill_match"] == 30
    assert result["scores"]["ats_compatibility"] == 42.0


def test_resume_analysis_exposes_conservative_structured_project_and_experience_fields(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.0, "not_available"))
    result = build_resume_summary(
        "Alex Example\nEXPERIENCE\nBackend Engineer at Acme | 2022 - 2024\nBuilt a Python API.\nPROJECTS\nResume Analyzer: Built with FastAPI and SQL.",
    )
    experience = result["resume"]["experience"][0]
    assert experience["role"] == "Backend Engineer"
    assert experience["company"] == "Acme"
    assert experience["start_date"] == "2022"
    project = result["resume"]["projects"][0]
    assert project["project_name"] == "Resume Analyzer"
    assert "FastAPI" in project["technologies"]

    education = build_resume_summary(
        "Alex Example\nEDUCATION\nBachelor of Technology in Computer Science | Example University | 2021 - 2025 | CGPA: 8.4",
    )["resume"]["education"][0]
    assert education["degree"] == "Bachelor of Technology"
    assert education["field"] == "Computer Science"
    assert education["institution"] == "Example University"
    assert education["graduation_year"] == "2025"


def test_scanned_pdf_uses_ocr_fallback_when_available(tmp_path, monkeypatch):
    from app.services import document_parser

    monkeypatch.setattr(document_parser, "extract_pdf_text", lambda _path: "")
    monkeypatch.setattr(document_parser, "extract_scanned_pdf_text", lambda _path: "SKILLS\nPython")
    result = document_parser.parse_resume_content("scan.pdf", b"%PDF-1.7 test")
    assert "Python" in result


def test_ocr_unavailable_returns_setup_guidance(monkeypatch):
    import pytesseract
    from app.services import document_parser

    def missing_tesseract():
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(document_parser, "TESSERACT_CMD", "")
    monkeypatch.setattr(pytesseract, "get_tesseract_version", missing_tesseract)
    try:
        document_parser.extract_scanned_pdf_text("unused.pdf")
    except ValueError as error:
        assert "Install Tesseract OCR" in str(error)
        assert "TESSERACT_CMD" in str(error)
    else:
        raise AssertionError("Missing Tesseract executable was not reported")


def test_role_catalog_covers_common_it_job_families():
    role_names = {item["role"] for item in list_role_profiles()}
    assert {"Backend Developer", "Frontend Developer", "DevOps Engineer", "Cybersecurity Analyst", "QA Automation Engineer"}.issubset(role_names)


def test_resume_upload_validation_checks_extension_and_file_signature():
    assert validate_resume_content("resume.PDF", b"%PDF-1.7 document") == ".pdf"
    try:
        validate_resume_content("resume.doc", b"not a supported format")
    except ValueError as error:
        assert "PDF or DOCX" in str(error)
    else:
        raise AssertionError("Unsupported DOC extension was accepted")

    try:
        validate_resume_content("resume.pdf", b"not a PDF")
    except ValueError as error:
        assert "valid PDF" in str(error)
    else:
        raise AssertionError("Invalid PDF signature was accepted")


def test_hybrid_job_match_breakdown_is_weighted_and_deterministic(monkeypatch):
    from app.services import resume_parser

    monkeypatch.setattr(resume_parser, "compute_semantic_similarity", lambda *_: (0.8, "sentence-transformers"))
    result = build_resume_summary(
        "Alex Example\nalex@example.com\nSKILLS\nPython\nEXPERIENCE\nBuilt APIs\nPROJECTS\nResume parser",
        "Python developer",
    )
    expected_score = round(sum(item["weight"] * item["score"] for item in result["match_breakdown"].values()) / 100)
    assert result["scores"]["compatibility"] == expected_score
    assert result["semantic_match_source"] == "sentence-transformers"
    assert sum(item["weight"] for item in result["match_breakdown"].values()) == 100


def test_ai_improvement_uses_labeled_rule_based_fallback(monkeypatch):
    from app.services import resume_improvement

    monkeypatch.setattr(resume_improvement, "AI_API_KEY", "")
    monkeypatch.setattr(resume_improvement, "AI_PROVIDER", "")
    result = improve_resume_text("Worked on a Python project.", "bullet point")
    assert result["mode"] == "rule-based"
    assert "AI enhancement unavailable" in result["notice"]
    assert result["improved_text"] == "Contributed to a Python project."


def test_history_and_comparison_use_persisted_analysis_records(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'history.db'}")
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(resume_routes, "SessionLocal", test_sessions)
    with test_sessions() as db:
        owner = UserRecord(email="owner@example.com", password_hash="test")
        other_user = UserRecord(email="other@example.com", password_hash="test")
        db.add_all([owner, other_user])
        db.flush()
        first = AnalysisRecord(owner_user_id=owner.id, filename="first.pdf", compatibility_score=60, ats_score=70, json_output=json.dumps({
            "scores": {"compatibility": 60, "ats_compatibility": 70, "skill_match": 50, "keyword_match": 55},
            "resume": {"skills": ["Python"], "sections_detected": ["skills"]},
        }))
        second = AnalysisRecord(owner_user_id=owner.id, filename="second.pdf", compatibility_score=80, ats_score=75, json_output=json.dumps({
            "scores": {"compatibility": 80, "ats_compatibility": 75, "skill_match": 80, "keyword_match": 65},
            "resume": {"skills": ["Python", "Docker"], "sections_detected": ["skills", "projects"]},
        }))
        db.add_all([first, second])
        db.add(AnalysisRecord(owner_user_id=other_user.id, filename="private.pdf", compatibility_score=99, json_output="{}"))
        db.commit()
        first_id, second_id = first.id, second.id
        owner_id, other_user_id = owner.id, other_user.id
    owner = UserRecord(id=owner_id, email="owner@example.com", password_hash="test")
    other_user = UserRecord(id=other_user_id, email="other@example.com", password_hash="test")

    history = resume_routes.list_analysis_history(owner)
    other_history = resume_routes.list_analysis_history(other_user)
    comparison = resume_routes.compare_saved_analyses(resume_routes.ComparePayload(
        first_analysis_id=first_id,
        second_analysis_id=second_id,
    ), owner)
    assert len(history) == 2
    assert len(other_history) == 1
    assert comparison["score_changes"]["compatibility"] == 20
    assert comparison["new_skills"] == ["Docker"]
    assert comparison["new_sections"] == ["projects"]
    clear_result = resume_routes.clear_analysis_history(owner)
    assert clear_result["deleted_count"] == 2
    assert resume_routes.list_analysis_history(owner) == []
    assert len(resume_routes.list_analysis_history(other_user)) == 1
    engine.dispose()


def test_password_hash_and_signed_token_validation():
    password_hash = hash_password("Long-strong-password-123")
    assert password_hash.startswith("scrypt$")
    assert verify_password("Long-strong-password-123", password_hash)
    assert not verify_password("wrong-password", password_hash)
    token = create_access_token(23, now=1000)
    assert decode_access_token(token, now=1001) == 23
    try:
        decode_access_token(token, now=1000 + 12 * 60 * 60)
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError("Expired token was accepted")
    body, signature = token.split(".")
    try:
        decode_access_token(f"{body}.{signature[:-1]}A", now=1001)
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError("Tampered token was accepted")


def test_account_registration_and_login_use_distinct_password_hashes(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'accounts.db'}")
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_routes, "SessionLocal", test_sessions)
    monkeypatch.setattr(auth_routes, "hash_password", hash_password)
    monkeypatch.setattr(auth_routes, "create_access_token", create_access_token)
    monkeypatch.setattr("app.services.auth_service.SessionLocal", test_sessions)

    credentials = auth_routes.CredentialsPayload(email="Person@Example.com", password="Long-strong-password-123")
    registered = auth_routes.register(credentials)
    logged_in = auth_routes.login(auth_routes.CredentialsPayload(email="person@example.com", password="Long-strong-password-123"))
    assert registered["user"]["email"] == "person@example.com"
    assert decode_access_token(registered["access_token"]) == registered["user"]["id"]
    assert logged_in["user"]["id"] == registered["user"]["id"]
    with test_sessions() as db:
        account = db.query(UserRecord).one()
        assert account.password_hash != "Long-strong-password-123"
        assert account.password_hash.startswith("scrypt$")
    engine.dispose()


def test_login_throttle_limits_repeated_bad_passwords(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'login-throttle.db'}")
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_routes, "SessionLocal", test_sessions)
    auth_routes._LOGIN_FAILURES.clear()
    payload = auth_routes.CredentialsPayload(email="unknown@example.com", password="Long-strong-password-123")
    for _ in range(5):
        try:
            auth_routes.login(payload)
        except HTTPException as error:
            assert error.status_code == 401
        else:
            raise AssertionError("Invalid credentials were accepted")
    try:
        auth_routes.login(payload)
    except HTTPException as error:
        assert error.status_code == 429
    else:
        raise AssertionError("Repeated failed logins were not throttled")
    auth_routes._LOGIN_FAILURES.clear()
    engine.dispose()


def test_account_deletion_removes_its_analyses_only(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'account-delete.db'}")
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_routes, "SessionLocal", test_sessions)
    with test_sessions() as db:
        target = UserRecord(email="target@example.com", password_hash="hash")
        other = UserRecord(email="other@example.com", password_hash="hash")
        db.add_all([target, other])
        db.flush()
        target_id, other_id = target.id, other.id
        db.add_all([
            AnalysisRecord(owner_user_id=target_id, filename="target.pdf", json_output="{}"),
            AnalysisRecord(owner_user_id=other_id, filename="other.pdf", json_output="{}"),
        ])
        db.commit()
    target = UserRecord(id=target_id, email="target@example.com", password_hash="hash")
    response = auth_routes.delete_current_account(target)
    assert response["deleted_analysis_count"] == 1
    with test_sessions() as db:
        assert db.query(UserRecord).filter(UserRecord.id == target_id).count() == 0
        assert db.query(AnalysisRecord).count() == 1
    engine.dispose()


def test_pdf_report_is_a_readable_pdf():
    import pymupdf

    pdf_bytes = generate_analysis_report({
        "resume": {"name": "Test Candidate", "skills": ["Python"], "sections_detected": ["skills"]},
        "scores": {"compatibility": 80, "ats_compatibility": 70},
        "matched_skills": ["Python"],
        "missing_skills": ["Docker"],
        "ats_analysis": {"checks": [{"status": "pass", "name": "Skills", "detail": "Skills heading detected."}]},
        "recommendations": ["Add evidence for Docker."],
        "summary": "Backend engineer.",
    }, "test.pdf")
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as report:
        extracted = "\n".join(page.get_text() for page in report)
    assert "Test Candidate" in extracted
    assert "compatibility" in extracted.lower()
    assert "Add evidence for Docker" in extracted
