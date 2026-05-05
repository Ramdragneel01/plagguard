"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    # LLM provider for humanisation ("openai" | "anthropic")
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "openai")
    )
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    # Model to use for humanisation
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    # Sentence-transformer model for embeddings
    embed_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBED_MODEL", "all-MiniLM-L6-v2"
        )
    )
    # Similarity threshold (0-1) above which a sentence is flagged
    similarity_threshold: float = field(
        default_factory=lambda: float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
    )
    # Maximum input length (characters)
    max_input_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_INPUT_LENGTH", "50000"))
    )
    # SQLite database path
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite:///./plagguard.db"
        )
    )
    # CORS origins
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")
    )
    # Search API key for web plagiarism checking (Google Custom Search)
    google_api_key: str = field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", "")
    )
    google_cse_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_CSE_ID", "")
    )


settings = Settings()
