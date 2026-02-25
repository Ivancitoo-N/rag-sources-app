"""
Embedding service using sentence-transformers (runs 100% locally).
Model is cached after first download (~90MB for all-MiniLM-L6-v2).
"""
from __future__ import annotations
import threading
import numpy as np
from config import settings


class EmbeddingService:
    _instance: "EmbeddingService | None" = None
    _model: "SentenceTransformer | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        """Load the embedding model (lazy loading)."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    print(f"[Embeddings] Loading model: {settings.embedding_model} ...")
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(settings.embedding_model)
                    print("[Embeddings] Model ready ✓")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts. Returns list of float vectors."""
        if self._model is None:
            self.load()
        # self._model is guaranteed to be set after load()
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

    def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two normalized vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        return float(np.dot(a, b))  # Already L2-normalized


embedding_service = EmbeddingService()
