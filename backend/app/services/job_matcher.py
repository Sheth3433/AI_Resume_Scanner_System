import re
from math import sqrt


def normalize_tokens(text: str):
    text = text.lower()
    return re.findall(r"[a-z0-9+.#]+", text)


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sqrt(sum(a * a for a in vec_a))
    mag_b = sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def vectorize(text: str):
    tokens = normalize_tokens(text)
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return sorted(counts.items())


def compute_similarity(resume_text: str, job_text: str) -> float:
    if not resume_text or not job_text:
        return 0.0
    resume_vector = vectorize(resume_text)
    job_vector = vectorize(job_text)
    resume_dict = dict(resume_vector)
    job_dict = dict(job_vector)
    common_tokens = set(resume_dict) & set(job_dict)
    if not common_tokens:
        return 0.0
    vec_a = [resume_dict.get(token, 0) for token in sorted(common_tokens)]
    vec_b = [job_dict.get(token, 0) for token in sorted(common_tokens)]
    return round(max(0.0, min(1.0, cosine_similarity(vec_a, vec_b))), 4)
