# Optional GPU image. Build context: ./backend
#
# UNTESTED: there is no GPU where this project was developed, so this file has
# never been built or run. It mirrors the CPU image on a CUDA runtime base and
# switches ASR to the GPU. Treat it as a starting point and verify before use.
#
#   docker build -f infra/docker/backend.gpu.Dockerfile -t ansit-backend:gpu backend
#   docker run --gpus all ... (mount artifacts as for the CPU image)
#
# Only ASR moves to the GPU. The speaker model (27 MB, ~170 ms on CPU) stays on
# ONNX Runtime CPU; moving it would need the onnxruntime-gpu package.

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS base
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3.11 python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN python3.11 -m pip install --no-cache-dir uv==0.11.32
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv UV_PYTHON=python3.11
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH" \
    ASR_DEVICE=cuda \
    ASR_COMPUTE_TYPE=float16 \
    QURAN_INDEX_PATH=/app/artifacts/quran_index.json.gz \
    ASR_MODEL_PATH=/app/artifacts/asr/tarteel-base \
    SPEAKER_MODEL_PATH=/app/artifacts/speaker/resnet34.onnx \
    GALLERY_PATH=/app/artifacts/gallery.npz \
    REGISTRY_PATH=/app/registry/reciters.json
RUN useradd --system --uid 10001 --no-create-home ansit
COPY app ./app
COPY alembic.ini docker-entrypoint.sh ./
RUN chmod 0555 docker-entrypoint.sh
USER ansit
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
