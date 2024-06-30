.PHONY: check
check: lint test

.PHONY: lint
lint:
	poetry run ruff format src/
	poetry run ruff check --fix --show-fixes src/
	poetry run mypy src/

.PHONY: test
test:
	poetry run pytest -m "not kubernetes" src/

.PHONY: pre-commit
pre-commit:
	pre-commit install --hook-type commit-msg

.PHONY: deps
deps:
	poetry install --all-extras --sync
