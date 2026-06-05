.PHONY: setup dev lint format test clean

setup:
	uv venv
	uv sync
	uv run pre-commit install

dev:
	docker compose up

lint:
	uv run ruff check --fix .
	uv run ruff format .

format:
	uv run ruff format .

test:
	uv run pytest

clean:
	docker compose down
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .venv -exec rm -rf {} +
