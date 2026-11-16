.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/docker-compose.yml
BACKEND := uv run --directory backend

.PHONY: help setup lint format typecheck test check up down logs ps data index gallery eval

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

gallery: ## Build the reciter gallery (Phase 3)
	@echo "make gallery: implemented in Phase 3" && exit 1

eval: ## Run the text-only matcher evaluation (writes ml/eval/reports/phase1.md)
	uv run --project backend python ml/eval/text_eval.py
