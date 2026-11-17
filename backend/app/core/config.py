"""Application settings, loaded from environment variables (see `.env.example`)."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- service ---
    app_env: Literal["dev", "test", "prod"] = "dev"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    allow_debug: bool = False
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    rate_limit_per_min: int = Field(default=20, ge=1)

    # --- stores (unset = not used / not checked by /readyz) ---
    database_url: str | None = None
    redis_url: str | None = None

    # --- matching ---
    # 76: lowest score with <= 1% false accepts on hard text negatives (Phase 1 report).
    # Provisional until re-calibrated on audio in Phase 2.
    match_threshold: float = Field(default=76.0, ge=0, le=100)
    ambiguity_delta: float = Field(default=2.0, ge=0)
    # Placeholder, NOT calibrated until Phase 3.
    reciter_threshold: float = Field(default=0.5, ge=-1, le=1)

    quran_index_path: str = "../ml/artifacts/quran_index.json.gz"

    # --- audio limits ---
    min_speech_sec: float = Field(default=1.5, gt=0)
    min_clip_sec: float = Field(default=3.0, gt=0)
    max_clip_sec: float = Field(default=15.0, gt=0)
    max_upload_mb: float = Field(default=2.0, gt=0)

    # --- models ---
    asr_model_path: str | None = None
    asr_beam_size: int = Field(default=5, ge=1)
    asr_device: Literal["cpu", "cuda"] = "cpu"
    asr_compute_type: str = "int8"
    cpu_threads_asr: int = Field(default=2, ge=1)
    cpu_threads_speaker: int = Field(default=2, ge=1)

    # --- speech detection and hallucination guards ---
    # Low on purpose: Silero under-detects recitation (see app/audio/vad.py).
    vad_threshold: float = Field(default=0.15, gt=0, lt=1)
    vad_trim_silence: bool = False
    asr_max_no_speech_prob: float = Field(default=0.6, ge=0, le=1)
    asr_min_avg_logprob: float = Field(default=-1.0, le=0)
    asr_max_compression_ratio: float = Field(default=2.4, gt=0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string: `CORS_ORIGINS=https://a.com,https://b.com`."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url", "redis_url", "asr_model_path", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
