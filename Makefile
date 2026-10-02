PNPM ?= pnpm

.PHONY: install dev dev-server dev-web test e2e lint format

install:
	uv sync --frozen
	$(PNPM) -C web install --frozen-lockfile

dev:
	$(MAKE) -j2 dev-server dev-web

dev-server:
	uv run kenji-server

dev-web:
	$(PNPM) -C web dev

test:
	uv run pytest
	uv run coverage report --include="src/kenji/domain/*" --fail-under=100
	$(PNPM) -C web test

e2e:
	$(PNPM) -C web e2e

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	$(PNPM) -C web lint
	$(PNPM) -C web typecheck
	$(PNPM) -C web format:check

format:
	uv run ruff check --fix .
	uv run ruff format .
	$(PNPM) -C web format
