"""Text preprocessing and statistics utilities."""

from __future__ import annotations

import math
import re
from collections import Counter


def split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex-based rules."""
    # Handle abbreviations to avoid false splits
    text = re.sub(r"(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Inc|Ltd)\.", r"\1<DOT>", text)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.replace("<DOT>", ".").strip() for s in sentences if len(s.strip()) > 5]


def get_ngrams(text: str, n: int = 3) -> list[tuple[str, ...]]:
    """Extract word-level n-grams from text."""
    words = _tokenise(text)
    if len(words) < n:
        return []
    return [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]


def _tokenise(text: str) -> list[str]:
    """Simple whitespace + punctuation tokeniser."""
    return re.findall(r"\b\w+\b", text.lower())


def compute_text_stats(text: str) -> dict:
    """Return word count, sentence count, vocabulary richness, readability."""
    words = _tokenise(text)
    sentences = split_sentences(text)
    word_count = len(words)
    sentence_count = max(len(sentences), 1)
    avg_sentence_length = word_count / sentence_count
    unique_words = set(words)
    unique_word_ratio = len(unique_words) / max(word_count, 1)

    # Flesch-Kincaid approximation
    syllable_count = sum(_count_syllables(w) for w in words)
    readability = (
        206.835
        - 1.015 * avg_sentence_length
        - 84.6 * (syllable_count / max(word_count, 1))
    )
    readability = max(0.0, min(100.0, readability))

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "unique_word_ratio": round(unique_word_ratio, 4),
        "readability_score": round(readability, 2),
    }


def _count_syllables(word: str) -> int:
    """Rough syllable counter for English words."""
    word = word.lower().rstrip("e")
    vowels = "aeiou"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(count, 1)


def ngram_overlap(text_a: str, text_b: str, n: int = 4) -> float:
    """Jaccard similarity between n-gram sets of two texts."""
    ng_a = set(get_ngrams(text_a, n))
    ng_b = set(get_ngrams(text_b, n))
    if not ng_a or not ng_b:
        return 0.0
    intersection = ng_a & ng_b
    union = ng_a | ng_b
    return len(intersection) / len(union)


def cosine_similarity_vectors(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
