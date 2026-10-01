from __future__ import annotations

from textwrap import wrap

import pymupdf


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 48
RIGHT = 547


def generate_analysis_report(analysis: dict, filename: str = "Resume analysis") -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = 52

    def new_page() -> None:
        nonlocal page, y
        page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        y = 52
        page.draw_line((LEFT, 38), (RIGHT, 38), color=(0.82, 0.82, 0.80), width=0.7)
        page.insert_text((LEFT, 30), "AI RESUME SCANNER  /  ANALYSIS REPORT", fontsize=8, color=(0.40, 0.40, 0.38))

    def add_text(value: str, *, size: float = 10, color: tuple[float, float, float] = (0.16, 0.16, 0.15), bold: bool = False, gap: float = 5) -> None:
        nonlocal y
        for line in wrap(str(value), width=88, break_long_words=True, break_on_hyphens=False) or [""]:
            if y > PAGE_HEIGHT - 54:
                new_page()
            page.insert_text((LEFT, y), line, fontname="hebo" if bold else "helv", fontsize=size, color=color)
            y += size + gap

    def add_section(title: str, lines: list[str]) -> None:
        nonlocal y
        y += 10
        add_text(title.upper(), size=9, color=(0.35, 0.35, 0.33), bold=True, gap=7)
        page.draw_line((LEFT, y - 2), (RIGHT, y - 2), color=(0.88, 0.88, 0.86), width=0.6)
        y += 7
        for line in lines:
            add_text(line, size=9, color=(0.25, 0.25, 0.24), gap=5)

    page.insert_text((LEFT, y), "RESUME ANALYSIS", fontsize=10, fontname="hebo", color=(0.36, 0.36, 0.34))
    y += 28
    page.insert_text((LEFT, y), str(analysis.get("resume", {}).get("name") or "Unknown Candidate")[:70], fontsize=22, fontname="hebo", color=(0.09, 0.09, 0.09))
    y += 24
    page.insert_text((LEFT, y), filename[:90], fontsize=9, color=(0.45, 0.45, 0.43))
    y += 18

    scores = analysis.get("scores", {})
    score_labels = (
        ("Job compatibility", "compatibility"),
        ("Estimated ATS compatibility", "ats_compatibility"),
        ("Semantic match", "semantic_match"),
        ("Skill match", "skill_match"),
        ("Keyword overlap", "keyword_match"),
    )
    add_section("Scores", [f"{label}: {scores.get(key, 0)}/100" for label, key in score_labels])

    resume = analysis.get("resume", {})
    add_section("Candidate details", [
        f"Email: {resume.get('email') or 'Not detected'}",
        f"Phone: {resume.get('phone') or 'Not detected'}",
        f"Sections: {', '.join(resume.get('sections_detected', [])) or 'Not detected'}",
    ])
    add_section("Skills", [
        f"Detected: {', '.join(resume.get('skills', [])) or 'None detected'}",
        f"Matched to job: {', '.join(analysis.get('matched_skills', [])) or 'None detected'}",
        f"Not detected in resume: {', '.join(analysis.get('missing_skills', [])) or 'None'}",
        *[
            f"Evidence - {item.get('skill')}: {item.get('evidence')} ({item.get('source_section', 'section not detected')})"
            for item in resume.get("skill_details", [])[:8]
        ],
    ])

    ats = analysis.get("ats_analysis", {})
    add_section("ATS checks", [
        f"{check.get('status', 'unknown').replace('_', ' ').title()} - {check.get('name', 'Check')}: {check.get('detail', '')}"
        for check in ats.get("checks", [])
    ] or ["No ATS checks were returned."])
    recommendations = [
        f"{item.get('title')}: {item.get('action')} Evidence: {item.get('evidence')}"
        for item in analysis.get("recommendation_details", [])
    ] or analysis.get("recommendations", [])
    add_section("Recommendations", recommendations or ["No recommendations returned."])
    add_section("Role suggestions", [
        f"{item.get('role')} - {item.get('match_score')}% overlap. {item.get('reason')} Missing signals: {', '.join(item.get('missing_skills', [])) or 'None'}"
        for item in analysis.get("role_recommendations", [])
    ] or ["Not enough detected skill evidence for role suggestions."])
    add_section("Resume summary", [analysis.get("summary") or "No summary text was extracted."])
    add_text("This estimated analysis is heuristic, does not predict a proprietary ATS, and should not replace a human review.", size=8, color=(0.45, 0.45, 0.43), gap=4)

    result = document.tobytes()
    document.close()
    return result