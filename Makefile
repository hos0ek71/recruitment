export TEST_DATABASE_URL ?= postgresql+psycopg://recruitment:recruitment@127.0.0.1:5433/recruitment_test

.PHONY: db-up db-test-reset check-backend check-web check

db-up:
	docker compose up -d --wait db

db-test-reset:
	cd backend && uv run python -m scripts.reset_test_db

check-backend:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest

check-web:
	@if [ -f web/package.json ]; then \
		pnpm -C web install --frozen-lockfile && pnpm -C web lint && pnpm -C web typecheck && pnpm -C web test; \
	else \
		echo "web 없음"; \
	fi

check: db-up check-backend check-web
