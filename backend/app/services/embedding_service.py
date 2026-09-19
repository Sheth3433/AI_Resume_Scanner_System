from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.config import MODEL_NAME

_MODEL = None


def get_embedding_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def embed_text(text: str):
    model = get_embedding_model()
    return model.encode(text, convert_to_numpy=True, normalize_embeddings=True)


def embed_texts(texts: list[str]):
    if not texts:
        return []
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
