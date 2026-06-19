# Squarebot

Squarebot is SQuaRE's Slack bot front end. It receives Slack events (Events
API) and interactivity payloads over HTTP and republishes them to Kafka topics
as JSON-serialized Pydantic models, so downstream Rubin microservices can react
to Slack activity without each one integrating with Slack directly.

## Repository layout

This is a **uv workspace** with a single root `uv.lock`:

- **Root — `squarebot` (the server).** FastAPI app under `src/squarebot/`,
  tests under `tests/`. Requires Python ≥3.14. Shipped as a Docker image; **not**
  published to PyPI.
- **`client/` — `rubin-squarebot` (the client library).** Pydantic models under
  `client/src/rubin/squarebot/` (import path `rubin.squarebot.models`), tests
  under `client/tests/`. Requires Python ≥3.13. **Published to PyPI.** The server
  depends on it via the workspace (`tool.uv.sources`).

Versioning is unified: one git tag (setuptools_scm) versions both the Docker
image and the client package.

## Development environment

- Python 3.14 (`.python-version`), managed with **uv**.
- `make init` — sync all dependency groups from the frozen `uv.lock` and install
  pre-commit hooks.
- `make update-deps` / `make update` — upgrade the lock + pre-commit hooks (and
  the pinned uv version via `scripts/update-uv-version.sh`).
- **Docker must be running** for the test suite — tests start their own Kafka
  broker via testcontainers (there is no `kafka-compose.yaml`).

## Common commands

Nox is provided by the `nox` dependency group through `nox-uv`, so sessions are
run via `uv run --only-group=nox nox` — **there is no bare `nox` on PATH.** The
`Makefile` wraps the common ones.

- `make test` / `uv run --only-group=nox nox -s test` — server suite; starts a
  testcontainers KRaft Kafka broker (needs Docker).
- `uv run --only-group=nox nox -s client_test` — client suite (run when you
  touch `client/`).
- `make lint` / `uv run --only-group=lint pre-commit run --all-files` — ruff and
  other pre-commit hooks.
- `make typing` / `uv run --only-group=nox nox -s typing` — mypy (strict).
- `uv run --only-group=nox nox -s docs` — build the Sphinx docs incl. OpenAPI.
- `make run` — run the app in dev mode against a testcontainers broker.
- Single test: `uv run --only-group=nox nox -s test -- tests/handlers/external_test.py::test_x`
  (posarg paths are relative to the repo root; `testpaths = ["tests"]`).

## Architecture notes (non-obvious)

- **Import-time singletons.** `src/squarebot/config.py` builds
  `config = Configuration()` at module import, and `src/squarebot/kafkarouter.py`
  builds the FastStream `KafkaRouter` from that config at import. Anything that
  imports the app therefore needs `KAFKA_BOOTSTRAP_SERVERS` and the Slack secrets
  (`SQUAREBOT_SLACK_SIGNING` / `_TOKEN` / `_APP_ID`) set **before** import. That
  is why the `test` and `run` nox sessions start the Kafka container and pass env
  vars into the pytest/uvicorn subprocess (see `_make_env_vars()` in
  `noxfile.py`) rather than using a conftest fixture.
- **Kafka, no Schema Registry.** The app uses a FastStream `KafkaRouter` to
  produce Slack events to Kafka topics as JSON-serialized Pydantic models. There
  is **no Schema Registry, no Avro, no kafkit.** The test `app` fixture runs the
  lifespan (which connects to the broker), so a live Kafka is required for the
  test suite — hence testcontainers.
- **Docs / OpenAPI.** `squarebot.main:create_openapi` imports the app (so it
  needs the env vars above) but does **not** start the lifespan, so the `docs`
  nox session can render the OpenAPI page without a running broker — it supplies
  the env vars via `_make_env_vars()`.

## Tooling conventions

- **Lint/format:** ruff, configured by `ruff-shared.toml` (canonical SQuaRE
  config, `target-version = "py314"`) extended by `[tool.ruff]` in
  `pyproject.toml`. Per-file ignores exist for `noxfile.py`,
  `src/squarebot/handlers/**` (FastAPI handlers skip docstrings), and `tests/**`.
- **pre-commit:** plain `pre-commit` (virtualenv backend). `pre-commit-uv` is
  **intentionally omitted** on Python 3.14 — its uv-created hook venvs fail
  pre-commit's health check; revisit once it supports 3.14. Hooks include
  `ruff-check`, pre-commit-hooks v6, and `uv-lock`.
- **Typing:** mypy in strict mode with the pydantic plugin;
  `mypy_path = ["src", "client/src"]`.
- **Docker:** uv-based multi-stage build on `python:3.14-slim-bookworm`
  (`COPY --from=ghcr.io/astral-sh/uv`, frozen `uv sync`, non-root `appuser`,
  runtime `uvicorn squarebot.main:app` on port 8080).
- **CI:** GitHub Actions use `astral-sh/setup-uv` + `uv run --only-group=nox nox`;
  the client publishes to PyPI on `release` (`working-directory: client`).
- **Changelog:** scriv fragments under `changelog.d/`.

## Validation reference

`.claude/skills/project-mechanics/SKILL.md` holds the authoritative command list
that automated (stoker) phases use for lint / typing / test / docs.
