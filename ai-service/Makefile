.PHONY: up down logs migrate makemigration worker test lint import-products import-enriched index-products create-qdrant setup

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm api alembic upgrade head

makemigration:
	docker compose run --rm api alembic revision --autogenerate -m "$(name)"

worker:
	docker compose run --rm worker python -m app.workers.rq_worker

test:
	pytest

lint:
	ruff check .

import-products:
	docker compose run --rm api python scripts/import_products.py "$(file)"

import-enriched:
	docker compose run --rm api python scripts/import_enriched.py "$(or $(file),/data/pipeline/preprocessor/enriched_products.jsonl)"

index-products:
	docker compose run --rm api python scripts/index_products_qdrant.py

create-qdrant:
	docker compose run --rm api python scripts/create_qdrant_collections.py

# Full setup: start services, run migrations, create Qdrant collection
setup: up
	@echo "Waiting for services to start..."
	@sleep 5
	$(MAKE) migrate
	$(MAKE) create-qdrant
	@echo "Setup complete. Import products with: make import-enriched file=<path>"
