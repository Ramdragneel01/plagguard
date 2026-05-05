"""Plagiarism detection engine.

Combines three detection strategies:
1. Sentence-level semantic similarity (sentence-transformers)
2. N-gram overlap analysis
3. Optional web search cross-referencing
"""

from __future__ import annotations

import logging
import re
from typing import Any

from backend.config import settings
from backend.utils.similarity import encode_sentences, pairwise_cosine
from backend.utils.text_processing import (
    compute_text_stats,
    ngram_overlap,
    split_sentences,
)

logger = logging.getLogger(__name__)


# ── reference corpus (in-memory for MVP) ───────────────────────────────
_reference_corpus: list[str] = []
_reference_embeddings = None


def load_reference_corpus(texts: list[str]) -> int:
    """Add texts to the in-memory reference corpus."""
    global _reference_corpus, _reference_embeddings
    sentences = []
    for t in texts:
        sentences.extend(split_sentences(t))
    _reference_corpus.extend(sentences)
    _reference_embeddings = encode_sentences(_reference_corpus)
    return len(_reference_corpus)


def _self_similarity_check(sentences: list[str], threshold: float) -> list[dict]:
    """Check similarity between the input sentences themselves (self-plagiarism)."""
    if len(sentences) < 2:
        return []

    embeddings = encode_sentences(sentences)
    sim_matrix = pairwise_cosine(embeddings, embeddings)

    flagged: list[dict] = []
    seen_pairs: set[tuple[int, int]] = set()
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            if (i, j) in seen_pairs:
                continue
            score = float(sim_matrix[i, j])
            if score >= threshold:
                flagged.append(
                    {
                        "sentence": sentences[i],
                        "similarity_score": round(score, 4),
                        "matched_source": f"[self-repeat] {sentences[j][:80]}…",
                        "start_idx": 0,
                        "end_idx": 0,
                    }
                )
                seen_pairs.add((i, j))
    return flagged


def _corpus_similarity_check(
    sentences: list[str], threshold: float
) -> list[dict]:
    """Check against loaded reference corpus."""
    global _reference_embeddings
    if _reference_embeddings is None or len(_reference_corpus) == 0:
        return []

    q_emb = encode_sentences(sentences)
    sim_matrix = pairwise_cosine(q_emb, _reference_embeddings)

    flagged: list[dict] = []
    import numpy as np

    for i, sent in enumerate(sentences):
        best_idx = int(np.argmax(sim_matrix[i]))
        best_score = float(sim_matrix[i, best_idx])
        if best_score >= threshold:
            flagged.append(
                {
                    "sentence": sent,
                    "similarity_score": round(best_score, 4),
                    "matched_source": _reference_corpus[best_idx][:120],
                    "start_idx": 0,
                    "end_idx": 0,
                }
            )
    return flagged


async def _web_search_check(sentences: list[str]) -> list[dict]:
    """Cross-reference sentences with Google Custom Search API."""
    if not settings.google_api_key or not settings.google_cse_id:
        logger.info("Web search skipped – no Google API key configured.")
        return []

    import httpx

    flagged: list[dict] = []
    # Only check a sample of sentences to stay within rate limits
    sample = sentences[:10]
    async with httpx.AsyncClient(timeout=15) as client:
        for sent in sample:
            query = sent[:128]
            url = (
                f"https://www.googleapis.com/customsearch/v1"
                f"?key={settings.google_api_key}"
                f"&cx={settings.google_cse_id}"
                f"&q={query}&num=3"
            )
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if items:
                        # Check snippet similarity via n-gram overlap
                        for item in items:
                            snippet = item.get("snippet", "")
                            overlap = ngram_overlap(sent, snippet, n=3)
                            if overlap > 0.3:
                                flagged.append(
                                    {
                                        "sentence": sent,
                                        "similarity_score": round(min(overlap * 1.5, 1.0), 4),
                                        "matched_source": item.get("link", "web"),
                                        "start_idx": 0,
                                        "end_idx": 0,
                                    }
                                )
                                break
            except Exception as exc:
                logger.warning("Web search failed for sentence: %s", exc)
    return flagged


def _locate_sentence(text: str, sentence: str) -> tuple[int, int]:
    """Find start and end character index of a sentence in the original text."""
    idx = text.find(sentence)
    if idx == -1:
        # Fuzzy fallback: try first 40 characters
        idx = text.find(sentence[:40])
    start = max(idx, 0)
    return start, start + len(sentence)


async def detect_plagiarism(
    text: str,
    check_web: bool = False,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Run full plagiarism detection pipeline and return results dict."""
    if threshold is None:
        threshold = settings.similarity_threshold

    sentences = split_sentences(text)
    stats = compute_text_stats(text)

    all_flagged: dict[str, dict] = {}  # keyed by sentence to deduplicate

    # 1. Self-similarity (repetition within the text)
    for match in _self_similarity_check(sentences, threshold):
        s, e = _locate_sentence(text, match["sentence"])
        match["start_idx"] = s
        match["end_idx"] = e
        key = match["sentence"]
        if key not in all_flagged or match["similarity_score"] > all_flagged[key]["similarity_score"]:
            all_flagged[key] = match

    # 2. Reference corpus check
    for match in _corpus_similarity_check(sentences, threshold):
        s, e = _locate_sentence(text, match["sentence"])
        match["start_idx"] = s
        match["end_idx"] = e
        key = match["sentence"]
        if key not in all_flagged or match["similarity_score"] > all_flagged[key]["similarity_score"]:
            all_flagged[key] = match

    # 3. Web search
    if check_web:
        for match in await _web_search_check(sentences):
            s, e = _locate_sentence(text, match["sentence"])
            match["start_idx"] = s
            match["end_idx"] = e
            key = match["sentence"]
            if key not in all_flagged or match["similarity_score"] > all_flagged[key]["similarity_score"]:
                all_flagged[key] = match

    flagged_list = sorted(all_flagged.values(), key=lambda m: m["similarity_score"], reverse=True)

    # Overall score = fraction of sentences flagged weighted by their scores
    if sentences:
        overall = sum(m["similarity_score"] for m in flagged_list) / len(sentences)
    else:
        overall = 0.0
    overall = round(min(overall, 1.0), 4)

    # Risk level
    if overall >= 0.6:
        risk = "critical"
    elif overall >= 0.4:
        risk = "high"
    elif overall >= 0.2:
        risk = "medium"
    else:
        risk = "low"

    return {
        "overall_similarity": overall,
        "risk_level": risk,
        "flagged_sentences": flagged_list,
        "text_stats": stats,
        "sentence_count_checked": len(sentences),
    }
