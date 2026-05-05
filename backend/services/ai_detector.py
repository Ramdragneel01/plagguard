"""AI-generated text detection.

Uses 10 statistical signals to estimate the probability that text is AI-generated:
1. Sentence-length uniformity (AI text has very even sentence lengths)
2. Burstiness (coefficient of variation of sentence lengths)
3. Connector / transition-word overuse
4. AI-signature vocabulary ("delve", "landscape", "crucial", etc.)
5. Contraction absence (AI rarely uses don't, can't, won't)
6. Average word length / formality
7. Sentence-opener repetition patterns
8. Personal-pronoun scarcity
9. Hedging-language density
10. Punctuation-pattern uniformity
"""

from __future__ import annotations

import math
import re
from collections import Counter

from backend.utils.text_processing import split_sentences, _tokenise, _count_syllables


# ── helper sets ────────────────────────────────────────────────────────
_CONNECTORS = {
    "however", "moreover", "furthermore", "additionally", "consequently",
    "therefore", "nevertheless", "nonetheless", "subsequently", "hence",
    "thus", "meanwhile", "likewise", "conversely", "alternatively",
    "specifically", "essentially", "fundamentally", "significantly",
    "notably", "importantly", "interestingly", "surprisingly",
    "undoubtedly", "arguably", "evidently", "presumably",
    "overall", "ultimately", "accordingly", "similarly",
}

# Words/phrases that LLMs overuse massively compared to humans
_AI_SIGNATURE_WORDS = {
    "delve", "delves", "delving",
    "tapestry", "multifaceted", "nuanced", "nuances",
    "landscape", "crucial", "pivotal", "paramount",
    "foster", "fosters", "fostering",
    "leverage", "leveraging", "leverages",
    "utilize", "utilizing", "utilizes", "utilization",
    "facilitate", "facilitating", "facilitates",
    "comprehensive", "intricate", "intricacies",
    "navigate", "navigating", "navigates",
    "underscore", "underscores", "underscoring",
    "realm", "encompasses", "encompassing",
    "streamline", "streamlining", "streamlines",
    "enhance", "enhancing", "enhances", "enhancement",
    "robust", "scalable", "seamless", "seamlessly",
    "cutting-edge", "cutting", "edge",
    "revolutionize", "revolutionizing", "revolutionizes",
    "transformative", "groundbreaking",
    "imperative", "indispensable",
    "harness", "harnessing", "harnesses",
    "bolster", "bolstering", "bolsters",
    "empower", "empowering", "empowers",
    "spearhead", "spearheading",
    "burgeoning", "plethora",
    "myriad", "diverse", "dynamic",
    "ecosystem", "paradigm",
    "holistic", "synergy",
    "stakeholder", "stakeholders",
    "proactive", "proactively",
    "endeavor", "endeavors",
    "adhere", "adhering",
    "optimize", "optimizing", "optimization",
    "mitigate", "mitigating", "mitigation",
    "resonate", "resonates", "resonating",
}

_HEDGING = {
    "may", "might", "could", "potentially", "possibly", "perhaps",
    "likely", "unlikely", "generally", "typically", "often",
    "tends", "suggest", "suggests", "indicating", "appears",
    "seemingly", "arguably", "presumably",
}

_PERSONAL_PRONOUNS = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours"}

_CONTRACTIONS_RE = re.compile(
    r"\b(?:don't|doesn't|didn't|isn't|aren't|wasn't|weren't|won't|wouldn't|"
    r"couldn't|shouldn't|can't|it's|that's|there's|they're|we're|you're|"
    r"i'm|i've|i'll|i'd|he's|she's|let's|who's|what's|here's|what's|"
    r"you'll|we'll|they'll|she'll|he'll|you'd|we'd|they'd|"
    r"hasn't|haven't|hadn't|mustn't|needn't|shan't)\b",
    re.IGNORECASE,
)

# Formulaic AI sentence starters
_AI_STARTERS = {
    "it is", "this is", "these are", "there are", "there is",
    "in today", "in the", "one of", "as a", "as we",
    "in an", "with the", "by leveraging", "by utilizing",
    "when it", "from the", "the importance",
}


# ── individual signal functions ────────────────────────────────────────

def _sentence_lengths(sentences: list[str]) -> list[int]:
    return [len(_tokenise(s)) for s in sentences]


def _compute_burstiness(sentences: list[str]) -> float:
    """Coefficient of variation of sentence lengths.
    Human text: typically 0.5–1.0+   AI text: typically 0.15–0.45
    """
    lengths = _sentence_lengths(sentences)
    if len(lengths) < 2:
        return 0.5
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.0
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    return round(std_dev / mean, 4)


def _compute_perplexity(text: str) -> float:
    """Trigram-based pseudo-perplexity. Lower = more predictable = more AI."""
    tokens = _tokenise(text)
    if len(tokens) < 10:
        return 50.0

    # Use trigrams for better signal
    trigrams = [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" for i in range(len(tokens) - 2)]
    freq = Counter(trigrams)
    total = len(trigrams)

    entropy = 0.0
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return round(2 ** (entropy * 0.5), 2)  # dampened to bring into usable range


def _connector_density(text: str) -> float:
    tokens = _tokenise(text)
    if not tokens:
        return 0.0
    count = sum(1 for t in tokens if t in _CONNECTORS)
    return count / len(tokens)


def _ai_vocabulary_density(text: str) -> float:
    """Fraction of tokens that are AI-signature words."""
    tokens = _tokenise(text)
    if not tokens:
        return 0.0
    count = sum(1 for t in tokens if t in _AI_SIGNATURE_WORDS)
    return count / len(tokens)


def _contraction_rate(text: str) -> float:
    """Contractions per 100 words. Humans use ~3-8, AI uses ~0-1."""
    tokens = _tokenise(text)
    if not tokens:
        return 0.0
    contractions = len(_CONTRACTIONS_RE.findall(text))
    return (contractions / len(tokens)) * 100


def _avg_word_length(text: str) -> float:
    """AI text tends toward longer, more formal words (avg 5.2+)."""
    tokens = _tokenise(text)
    if not tokens:
        return 4.5
    return sum(len(t) for t in tokens) / len(tokens)


def _sentence_start_pattern_score(sentences: list[str]) -> float:
    """Measures how formulaic sentence openings are (0 = all unique, 1 = all same).
    Also penalises AI-typical starters.
    """
    if len(sentences) < 2:
        return 0.3

    starters: list[str] = []
    ai_starter_count = 0
    for s in sentences:
        words = _tokenise(s)
        if not words:
            continue
        opener = words[0]
        starters.append(opener)
        # Check two-word opener against AI starters
        two_word = " ".join(words[:2]) if len(words) >= 2 else ""
        if two_word in _AI_STARTERS:
            ai_starter_count += 1

    if not starters:
        return 0.3

    unique_ratio = len(set(starters)) / len(starters)
    repetition_score = 1.0 - unique_ratio  # higher = more repetitive = more AI
    ai_starter_ratio = ai_starter_count / len(sentences)

    return (repetition_score * 0.5) + (ai_starter_ratio * 0.5)


def _personal_pronoun_rate(text: str) -> float:
    """Personal pronouns per 100 words. Humans: 3-10+, AI: 0-2."""
    tokens = _tokenise(text)
    if not tokens:
        return 3.0
    count = sum(1 for t in tokens if t in _PERSONAL_PRONOUNS)
    return (count / len(tokens)) * 100


def _hedging_density(text: str) -> float:
    """Hedging words per 100 words. AI overuses hedging (2-5%), humans ~1-2%."""
    tokens = _tokenise(text)
    if not tokens:
        return 0.0
    count = sum(1 for t in tokens if t in _HEDGING)
    return (count / len(tokens)) * 100


def _sentence_length_uniformity(sentences: list[str]) -> float:
    """What fraction of sentences are within ±30% of the mean length.
    AI text: 70-95% of sentences are near mean. Human: 40-65%.
    """
    lengths = _sentence_lengths(sentences)
    if len(lengths) < 3:
        return 0.5
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.5
    lower = mean * 0.7
    upper = mean * 1.3
    near_mean = sum(1 for l in lengths if lower <= l <= upper)
    return near_mean / len(lengths)


# ── main detection function ────────────────────────────────────────────

def detect_ai(text: str) -> dict:
    """Run all AI detection heuristics and return a combined verdict.

    Returns:
        {
            "is_ai_generated": bool,
            "ai_probability": float (0-1),
            "perplexity_score": float,
            "burstiness_score": float,
        }
    """
    sentences = split_sentences(text)
    tokens = _tokenise(text)
    n_tokens = len(tokens)

    # Compute all signals
    perplexity = _compute_perplexity(text)
    burstiness = _compute_burstiness(sentences)
    connector_den = _connector_density(text)
    ai_vocab_den = _ai_vocabulary_density(text)
    contraction_rt = _contraction_rate(text)
    avg_wlen = _avg_word_length(text)
    start_pattern = _sentence_start_pattern_score(sentences)
    pronoun_rt = _personal_pronoun_rate(text)
    hedge_den = _hedging_density(text)
    uniformity = _sentence_length_uniformity(sentences)

    # ── Score each signal from 0 (human) to 1 (AI) ────────────────────

    scores: list[tuple[float, float]] = []  # (score, weight)

    # 1. Burstiness: lower = more AI  (weight: 0.14)
    if burstiness < 0.20:
        s = 0.95
    elif burstiness < 0.35:
        s = 0.80
    elif burstiness < 0.50:
        s = 0.55
    elif burstiness < 0.65:
        s = 0.30
    else:
        s = 0.03
    scores.append((s, 0.14))

    # 2. Sentence-length uniformity: higher = more AI  (weight: 0.12)
    if uniformity > 0.85:
        s = 0.95
    elif uniformity > 0.70:
        s = 0.75
    elif uniformity > 0.55:
        s = 0.45
    else:
        s = 0.03
    scores.append((s, 0.12))

    # 3. Connector density  (weight: 0.12)
    if connector_den > 0.05:
        s = 0.95
    elif connector_den > 0.03:
        s = 0.80
    elif connector_den > 0.015:
        s = 0.55
    elif connector_den > 0.01:
        s = 0.30
    else:
        s = 0.02
    scores.append((s, 0.12))

    # 4. AI signature vocabulary  (weight: 0.14) — strongest signal
    if ai_vocab_den > 0.06:
        s = 0.98
    elif ai_vocab_den > 0.04:
        s = 0.90
    elif ai_vocab_den > 0.025:
        s = 0.75
    elif ai_vocab_den > 0.01:
        s = 0.55
    elif ai_vocab_den > 0.005:
        s = 0.35
    else:
        s = 0.01
    scores.append((s, 0.14))

    # 5. Contraction absence  (weight: 0.10)
    if contraction_rt < 0.2:
        s = 0.85
    elif contraction_rt < 1.0:
        s = 0.60
    elif contraction_rt < 2.0:
        s = 0.35
    else:
        s = 0.04
    scores.append((s, 0.10))

    # 6. Average word length / formality  (weight: 0.08)
    # Technical content (AI, medicine, law) legitimately has longer words — raise thresholds
    if avg_wlen > 5.8:
        s = 0.85
    elif avg_wlen > 5.3:
        s = 0.65
    elif avg_wlen > 5.1:
        s = 0.35
    else:
        s = 0.03
    scores.append((s, 0.08))

    # 7. Sentence-start patterns  (weight: 0.10)
    if start_pattern > 0.6:
        s = 0.90
    elif start_pattern > 0.4:
        s = 0.70
    elif start_pattern > 0.25:
        s = 0.45
    else:
        s = 0.03
    scores.append((s, 0.10))

    # 8. Personal pronoun absence  (weight: 0.08)
    if pronoun_rt < 0.3:
        s = 0.80
    elif pronoun_rt < 1.0:
        s = 0.60
    elif pronoun_rt < 2.0:
        s = 0.35
    else:
        s = 0.03
    scores.append((s, 0.08))

    # 9. Hedging density  (weight: 0.06)
    if hedge_den > 4.0:
        s = 0.90
    elif hedge_den > 2.5:
        s = 0.70
    elif hedge_den > 1.5:
        s = 0.45
    else:
        s = 0.03
    scores.append((s, 0.06))

    # 10. Perplexity  (weight: 0.06) — unreliable for short texts (< 10 sentences)
    if len(sentences) < 10:
        s = 0.25  # not enough data for reliable perplexity — use neutral score
    elif perplexity < 15:
        s = 0.90
    elif perplexity < 30:
        s = 0.65
    elif perplexity < 50:
        s = 0.40
    else:
        s = 0.03
    scores.append((s, 0.06))

    # ── Weighted sum ──────────────────────────────────────────────────
    ai_probability = sum(s * w for s, w in scores)

    # Normalize weights (they should sum to 1.0 but just in case)
    total_weight = sum(w for _, w in scores)
    ai_probability = ai_probability / total_weight

    # Boost: if 4+ signals score above 0.7, bump probability
    high_signals = sum(1 for s, _ in scores if s >= 0.70)
    if high_signals >= 6:
        ai_probability = min(ai_probability * 1.20, 0.99)
    elif high_signals >= 4:
        ai_probability = min(ai_probability * 1.10, 0.97)

    ai_probability = round(min(max(ai_probability, 0.0), 1.0), 4)

    return {
        "is_ai_generated": ai_probability >= 0.50,
        "ai_probability": ai_probability,
        "perplexity_score": perplexity,
        "burstiness_score": burstiness,
    }
