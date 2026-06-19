.PHONY: help
help:
	@echo "Make targets for Squarebot:"
	@echo "make init - Set up dev environment"
	@echo "make update - Update pinned dependencies and run make init"
	@echo "make update-deps - Update pinned dependencies"
	@echo "make lint - Lint the code with pre-commit"
	@echo "make typing - Run mypy"
	@echo "make test - Run the test suite (requires Docker for Kafka)"
	@echo "make run - Run the application in development mode"

.PHONY: init
init:
	uv sync --frozen --all-groups
	uv run --only-group=lint pre-commit install

.PHONY: update
update: update-deps init

.PHONY: update-deps
update-deps:
	uv lock --upgrade
	uv run --only-group=lint pre-commit autoupdate
	./scripts/update-uv-version.sh

.PHONY: lint
lint:
	uv run --only-group=lint pre-commit run --all-files

.PHONY: typing
typing:
	uv run --only-group=nox nox -s typing

.PHONY: test
test:
	uv run --only-group=nox nox -s test

.PHONY: run
run:
	uv run --only-group=nox nox -s run
