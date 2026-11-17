"""Application settings, loaded from environment variables (see `.env.example`)."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# From the Phase 3 evaluation (ml/eval/reports/phase3.md, "Shipped setting").
RECITER_THRESHOLD_DEFAULT = 0.725
RECITER_MARGIN_DEFAULT = 0.12


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
    trust_proxy_headers: bool = False
    """Take the client IP from X-Forwarded-For. Only behind a proxy you control."""

    load_models: bool = True
    """Load the index, models and gallery at startup. Off only in tests."""
    reciter_enabled: bool = True
    """Run the reciter branch. When off, every reciter is reported as unknown."""
    max_concurrent_identify: int = Field(default=2, ge=1)
    """How many identify requests may run the models at the same time. Each one
    uses CPU_THREADS_ASR + CPU_THREADS_SPEAKER threads."""
    identify_queue_timeout_sec: float = Field(default=10.0, gt=0)
    ambiguous_ttl_sec: int = Field(default=300, ge=10)
    """How long an ambiguous result's candidate positions are kept for "listen longer"."""

    # --- stores (unset = not used / not checked by /readyz) ---
    database_url: str | None = None
    redis_url: str | None = None

    # --- matching ---
    # 76: lowest score with <= 1% false accepts on hard text negatives (Phase 1 report).
    # Provisional until re-calibrated on audio in Phase 2.
    match_threshold: float = Field(default=76.0, ge=0, le=100)
    ambiguity_delta: float = Field(default=2.0, ge=0)
    # Reciter is "identified" only if the best score reaches the threshold AND
    # leads the runner-up by the margin. Calibrated in Phase 3 (see its report).
    reciter_threshold: float = Field(default=RECITER_THRESHOLD_DEFAULT, ge=-1, le=1)
    reciter_min_margin: float = Field(default=RECITER_MARGIN_DEFAULT, ge=0, le=2)

    quran_index_path: str = "../ml/artifacts/quran_index.json.gz"
    speaker_model_path: str = "../ml/artifacts/speaker/resnet34.onnx"
    gallery_path: str | None = "../ml/artifacts/gallery.npz"
    registry_path: str | None = "../ml/registry/reciters.json"
    """Gallery and registry files, used when the database has no gallery
    (development without Postgres)."""

    # --- audio limits ---
    min_speech_sec: float = Field(default=1.5, gt=0)
    min_clip_sec: float = Field(default=3.0, gt=0)
    max_clip_sec: float = Field(default=15.0, gt=0)
    max_upload_mb: float = Field(default=2.0, gt=0)

    # --- models ---
    asr_model_path: str | None = "../ml/artifacts/asr/tarteel-base"
    asr_beam_size: int = Field(default=5, ge=1)
    asr_device: Literal["cpu", "cuda"] = "cpu"
    asr_compute_type: str = "int8"
    # The two branches of a request run at the same time. Measured on 4 vCPU
    # (Phase 4 load test): 2 ASR threads is faster than 3 or 4 once the speaker
    # branch runs alongside, and leaves room for a second request in parallel.
    cpu_threads_asr: int = Field(default=2, ge=1)
    cpu_threads_speaker: int = Field(default=1, ge=1)

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

    @field_validator(
        "database_url",
        "redis_url",
        "asr_model_path",
        "gallery_path",
        "registry_path",
        mode="before",
    )
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
