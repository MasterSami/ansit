.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/docker-compose.yml
BACKEND := uv run --directory backend

.PHONY: help setup lint format typecheck test check up down logs ps data index models speaker-model registry gallery gallery-db migrate serve loadtest eval eval-audio eval-reciter

help: ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend deps and git hooks
	uv sync --directory backend
	@test -f .env || cp .env.example .env
	uvx pre-commit install

lint: ## ruff check + format check (backend, ml)
	$(BACKEND) ruff check ..
	$(BACKEND) ruff format --check ..

format: ## Auto-format and auto-fix
	$(BACKEND) ruff check --fix ..
	$(BACKEND) ruff format ..

typecheck: ## mypy (strict on app/)
	$(BACKEND) mypy

test: ## Backend tests
	$(BACKEND) pytest -q

check: lint typecheck test ## Everything CI runs for the backend

up: ## Start postgres+pgvector, redis and the backend
	$(COMPOSE) up -d --build --wait

down: ## Stop the stack (keeps the database volume)
	$(COMPOSE) down

logs: ## Follow backend logs
	$(COMPOSE) logs -f backend

ps: ## Service status
	$(COMPOSE) ps

data: ## Download Quran text + metadata from Tanzil
	uv run --project backend python ml/scripts/download_quran.py

index: ## Build the Quran search index artifact
	uv run --project backend python ml/scripts/build_index.py

speaker-model: ## Download + verify the speaker embedding model (needs the `ml` group)
	uv run --project backend --group ml python ml/scripts/fetch_speaker_model.py

registry: ## Rebuild ml/registry/reciters.json from mp3quran + EveryAyah
	uv run --project backend python ml/scripts/build_registry.py

gallery: ## Build the reciter gallery (add RECITER=id to add/refresh one reciter)
	uv run --project backend --group ml python ml/scripts/build_gallery.py $(if $(RECITER),--reciter $(RECITER))

gallery-db: ## Load the registry + gallery into Postgres (uses DATABASE_URL; add RECITER=id for one)
	uv run --project backend python ml/scripts/load_gallery_db.py $(if $(RECITER),--reciter $(RECITER))

serve: ## Run the API locally without Docker (needs the artifacts; no Postgres/Redis required)
	uv run --directory backend uvicorn app.main:create_app --factory --port $(or $(PORT),8000)

loadtest: ## Locust load test against a running server (HOST=..., USERS=...)
	uvx locust -f infra/locust/locustfile.py --headless --host $(or $(HOST),http://localhost:8000) \
		-u $(or $(USERS),2) -r $(or $(USERS),2) -t $(or $(DURATION),75s) --only-summary

migrate: ## Apply database migrations (uses DATABASE_URL)
	uv run --directory backend alembic upgrade head

models: ## Download + convert the ASR models to CTranslate2 (needs the `ml` group)
	uv run --project backend --group ml python ml/scripts/convert_models.py --all

eval: ## Run the text-only matcher evaluation (writes ml/eval/reports/phase1.md)
	uv run --project backend python ml/eval/text_eval.py

eval-audio: ## Build the audio eval set, run it, write ml/eval/reports/phase2.md (~1 h CPU)
	uv run --project backend --group ml python ml/eval/build_audio_eval.py
	uv run --project backend python ml/eval/audio_eval.py run
	uv run --project backend python ml/eval/audio_eval.py report

eval-reciter: ## Reciter identification evaluation (writes ml/eval/reports/phase3.md)
	uv run --project backend python ml/eval/reciter_eval.py
