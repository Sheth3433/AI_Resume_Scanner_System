def calculate_compatibility(similarity: float, details: dict) -> float:
    matched = len(details.get("matched_skills", []))
    missing = len(details.get("missing_skills", []))
    score = similarity * 70 + min(matched * 8, 24) - min(missing * 4, 16)
    score = max(0, min(100, round(score)))
    return score
