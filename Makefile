.PHONY: help dev down test migrate lint format backend-shell db-shell

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services in development mode
	docker compose up --build

down: ## Stop all services
	docker compose down

test: ## Run backend tests
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	docker compose exec backend pytest tests/unit/ -v

test-integration: ## Run integration tests only
	docker compose exec backend pytest tests/integration/ -v

migrate: ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

makemigration: ## Create a new Alembic migration (usage: make makemigration msg="add users table")
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

lint: ## Run ruff + mypy
	docker compose exec backend ruff check app/ tests/
	docker compose exec backend mypy app/

format: ## Auto-format with ruff
	docker compose exec backend ruff format app/ tests/

backend-shell: ## Open a shell inside the backend container
	docker compose exec backend bash

db-shell: ## Open psql inside postgres container
	docker compose exec postgres psql -U axonhis -d axonhis

logs: ## Tail all service logs
	docker compose logs -f
