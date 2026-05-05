"""Pydantic request / response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── enums ──────────────────────────────────────────────────────────────
class HumanizeLevel(str, Enum):
    light = "light"
    moderate = "moderate"
    heavy = "heavy"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ── requests ───────────────────────────────────────────────────────────
class DetectRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=50000)
    check_web: bool = Field(False, description="Also search the web for matches")


class HumanizeRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=50000)
    level: HumanizeLevel = HumanizeLevel.moderate
    preserve_keywords: list[str] = Field(default_factory=list)


class FullPipelineRequest(BaseModel):
    """Run detect → humanize → re-detect in one call."""
    text: str = Field(..., min_length=20, max_length=50000)
    humanize_level: HumanizeLevel = HumanizeLevel.moderate
    check_web: bool = False


# ── sub-models ─────────────────────────────────────────────────────────
class SentenceMatch(BaseModel):
    sentence: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    matched_source: Optional[str] = None
    start_idx: int
    end_idx: int


class AIDetectionResult(BaseModel):
    is_ai_generated: bool
    ai_probability: float = Field(..., ge=0.0, le=1.0)
    perplexity_score: float
    burstiness_score: float


class TextStats(BaseModel):
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    unique_word_ratio: float
    readability_score: float


# ── responses ──────────────────────────────────────────────────────────
class DetectResponse(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    overall_similarity: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    flagged_sentences: list[SentenceMatch]
    ai_detection: AIDetectionResult
    text_stats: TextStats
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HumanizeResponse(BaseModel):
    original_text: str
    humanized_text: str
    changes_made: int
    level: HumanizeLevel
    ai_detection_before: AIDetectionResult
    ai_detection_after: AIDetectionResult


class PipelineResponse(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    original_detection: DetectResponse
    humanized_text: str
    post_humanize_detection: DetectResponse
    improvement_percent: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    models_loaded: bool = False
