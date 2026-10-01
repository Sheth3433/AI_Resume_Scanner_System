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
    vocabulary = sorted(set(resume_dict) | set(job_dict))
    if not vocabulary:
        return 0.0
    vec_a = [resume_dict.get(token, 0) for token in vocabulary]
    vec_b = [job_dict.get(token, 0) for token in vocabulary]
    return round(max(0.0, min(1.0, cosine_similarity(vec_a, vec_b))), 4)


def compute_semantic_similarity(resume_text: str, job_text: str) -> tuple[float, str]:
    if not resume_text or not job_text:
        return 0.0, "not_available"
    try:
        from app.services.embedding_service import embed_texts

        embeddings = embed_texts([resume_text, job_text])
        score = float(embeddings[0] @ embeddings[1])
        return round(max(0.0, min(1.0, score)), 4), "sentence-transformers"
    except Exception:
        return compute_similarity(resume_text, job_text), "token-overlap fallback"
