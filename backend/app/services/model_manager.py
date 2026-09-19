from __future__ import annotations

import os

from app.config import MODEL_NAME


class ModelManager:
    def __init__(self):
        self.model_name = MODEL_NAME
        self.model = None
        self.device = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"

    def load(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device=self.device)
        return self.model

    def encode(self, text):
        model = self.load()
        return model.encode(text, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
