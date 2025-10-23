.PHONY: check
check: lint test

.PHONY: lint
lint:
	uv run ruff format
	uv run ruff check --fix --show-fixes
	uv run mypy src/ tests/

.PHONY: test
test:
	uv run pytest -m "not kubernetes"

.PHONY: pre-commit
pre-commit:
	pre-commit install --hook-type commit-msg

.PHONY: deps
deps:
	uv install --all-extras --sync
