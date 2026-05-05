"""Embedding-based similarity engine."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from backend.config import settings

logger = logging.getLogger(__name__)

_model: "SentenceTransformer | None" = None


def _load_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", settings.embed_model)
        _model = SentenceTransformer(settings.embed_model)
        logger.info("Embedding model loaded.")
    return _model


def encode_sentences(sentences: list[str]) -> np.ndarray:
    """Return (N, dim) float32 array of sentence embeddings."""
    model = _load_model()
    return model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)


def pairwise_cosine(embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
    """Cosine similarity matrix (M, N) between two embedding matrices."""
    # Normalise
    a_norm = embeddings_a / (np.linalg.norm(embeddings_a, axis=1, keepdims=True) + 1e-9)
    b_norm = embeddings_b / (np.linalg.norm(embeddings_b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def find_best_matches(
    query_sentences: list[str],
    reference_sentences: list[str],
    threshold: float | None = None,
) -> list[dict]:
    """For each query sentence return the best matching reference and its score."""
    if threshold is None:
        threshold = settings.similarity_threshold

    if not query_sentences or not reference_sentences:
        return []

    q_emb = encode_sentences(query_sentences)
    r_emb = encode_sentences(reference_sentences)
    sim_matrix = pairwise_cosine(q_emb, r_emb)

    results = []
    for i, q_sent in enumerate(query_sentences):
        best_idx = int(np.argmax(sim_matrix[i]))
        best_score = float(sim_matrix[i, best_idx])
        results.append(
            {
                "query": q_sent,
                "best_match": reference_sentences[best_idx],
                "score": round(best_score, 4),
                "flagged": best_score >= threshold,
            }
        )
    return results


def is_model_loaded() -> bool:
    return _model is not None
