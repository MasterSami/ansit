# CPU image for the Ansit backend. Build context: ./backend
#
# Model files are NOT in the repository. Two ways to give them to the container:
#
#   mounted (default target, `runtime`):
#     docker build -f infra/docker/backend.Dockerfile -t ansit-backend backend
#     and mount ml/artifacts at /app/artifacts and ml/registry at /app/registry
#     (infra/docker-compose.yml does this).
#
#   baked in (target `baked`):
#     docker build -f infra/docker/backend.Dockerfile --target baked \
#         --build-context artifacts=ml/artifacts --build-context registry=ml/registry \
#         -t ansit-backend:baked backend
#
# Build the artifacts first: make data index models speaker-model gallery

FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv==0.11.32
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS base
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    QURAN_INDEX_PATH=/app/artifacts/quran_index.json.gz \
    ASR_MODEL_PATH=/app/artifacts/asr/tarteel-base \
    SPEAKER_MODEL_PATH=/app/artifacts/speaker/resnet34.onnx \
    GALLERY_PATH=/app/artifacts/gallery.npz \
    REGISTRY_PATH=/app/registry/reciters.json
RUN useradd --system --uid 10001 --no-create-home ansit
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY alembic.ini docker-entrypoint.sh ./
RUN chmod 0555 docker-entrypoint.sh
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]
CMD ["./docker-entrypoint.sh"]

# Models copied into the image: larger, but self-contained.
FROM base AS baked
COPY --from=artifacts quran_index.json.gz gallery.npz /app/artifacts/
COPY --from=artifacts asr/tarteel-base /app/artifacts/asr/tarteel-base
COPY --from=artifacts speaker/resnet34.onnx /app/artifacts/speaker/resnet34.onnx
COPY --from=registry reciters.json /app/registry/reciters.json
USER ansit

# Default: models mounted at run time.
FROM base AS runtime
USER ansit
