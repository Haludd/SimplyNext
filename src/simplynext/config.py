"""Runtime configuration for the SimplyNext backend.

Only non-secret application settings live here. AWS credentials are deliberately
left to the standard AWS credential provider chain and are never model fields.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from simplynext.contracts import SignLanguage

DEFAULT_BEDROCK_MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


class Settings(BaseSettings):
    """Non-secret settings loaded from ``SIMPLYNEXT_`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="SIMPLYNEXT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SimplyNext Backend"
    environment: Literal["development", "test", "production"] = "development"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65_535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_prefix: str = "/v1"
    allowed_origins: Annotated[tuple[str, ...], NoDecode] = (
        "http://localhost:3000",
        "http://localhost:8080",
    )

    session_ttl_seconds: int = Field(default=900, ge=30, le=86_400)
    max_batch_frames: int = Field(default=8, ge=1, le=32)
    target_fps: int = Field(default=20, ge=1, le=60)
    max_queued_frames: int = Field(default=240, ge=8, le=10_000)
    max_active_sessions: int = Field(default=128, ge=1, le=10_000)
    http_max_body_bytes: int = Field(default=262_144, ge=4_096, le=4_194_304)
    websocket_max_message_bytes: int = Field(
        default=1_048_576,
        ge=16_384,
        le=16_777_216,
    )
    # CTR v1 freezes this transport ceiling. A different value requires a new
    # schema version rather than a stricter deployment-specific dialect.
    gloss_lattice_max_message_bytes: Literal[32_768] = 32_768
    max_lattices_per_session: int = Field(default=100, ge=1, le=10_000)
    max_lattices_per_minute: int = Field(default=30, ge=1, le=600)
    max_lattices_per_minute_global: int = Field(default=120, ge=1, le=10_000)
    max_concurrent_agent_runs: int = Field(default=4, ge=1, le=64)
    agent_queue_timeout_seconds: float = Field(default=2.0, ge=0.1, le=30.0)
    lattice_websocket_idle_timeout_seconds: float = Field(
        default=120.0,
        ge=5.0,
        le=3_600.0,
    )

    template_bundle_path: Path | None = None
    caption_templates_path: Path | None = None
    recognition_language: SignLanguage = SignLanguage.ASL
    min_recognition_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    min_recognition_margin: float = Field(default=0.15, ge=0.0, le=1.0)
    min_landmark_coverage: float = Field(default=0.75, ge=0.0, le=1.0)
    bedrock_enabled: bool = False
    aws_region: str = "ap-southeast-1"
    bedrock_model_id: str = DEFAULT_BEDROCK_MODEL_ID
    bedrock_connect_timeout_seconds: float = Field(default=5.0, ge=0.1, le=60.0)
    bedrock_read_timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    bedrock_total_max_attempts: int = Field(default=3, ge=1, le=10)
    agent_max_revisions: int = Field(default=1, ge=0, le=1)
    enable_hypothesis_replay_endpoint: bool = False

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("/"):
            raise ValueError("api_prefix must begin with '/'")
        if value != "/" and value.endswith("/"):
            raise ValueError("api_prefix must not end with '/'")
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @field_validator("template_bundle_path", "caption_templates_path", mode="before")
    @classmethod
    def empty_path_is_unconfigured(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("bedrock_model_id", mode="before")
    @classmethod
    def use_default_model_for_blank_value(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return DEFAULT_BEDROCK_MODEL_ID
        return value

    @field_validator("host", "aws_region", "bedrock_model_id", "app_name")
    @classmethod
    def reject_empty_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @model_validator(mode="after")
    def lattice_limit_must_fit_websocket_limit(self) -> Settings:
        if self.gloss_lattice_max_message_bytes > self.websocket_max_message_bytes:
            raise ValueError(
                "gloss_lattice_max_message_bytes cannot exceed websocket_max_message_bytes"
            )
        return self

    @property
    def cors_origins(self) -> tuple[str, ...]:
        """Compatibility name used by some FastAPI examples."""

        return self.allowed_origins

    @property
    def recognition_confidence_threshold(self) -> float:
        return self.min_recognition_confidence

    @property
    def recognition_margin_threshold(self) -> float:
        return self.min_recognition_margin


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""

    return Settings()
