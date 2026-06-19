---
name: project-mechanics
description: Project-specific build/test/lint/typing commands for this repo. Read this skill at the start of any phase that runs validation (`stoker-work`, `stoker-fixup`, `stoker-rebase`).
---

# Project mechanics

This file is the source of truth for how this repo runs tests, lint,
and type-checking. Profile-shipped phase skills read it at the start
of each phase and use the named commands verbatim.

This is a **uv workspace** (one root `uv.lock`): the repo root is the
`squarebot` server package (`src/squarebot/`, tests in `tests/`) and
`client/` is the lone workspace member, the published `rubin-squarebot`
client (`client/src/rubin/squarebot/`, tests in `client/tests/`). Nox is
provided by the `nox` dependency group via `nox-uv`, so every nox session
is invoked through `uv run --only-group=nox nox`. There is no global
`nox` on PATH — never call bare `nox`.

## Test commands

- `focused_test`: `uv run --only-group=nox nox -s test -- <pytest args>`
  (e.g. `uv run --only-group=nox nox -s test -- tests/handlers/external_test.py::test_event`)
- `complete_test`: `uv run --only-group=nox nox -s test`

The `test` session starts its own **Kafka broker via testcontainers**
(KRaft mode) — **Docker must be running**, but you do NOT start a broker
yourself (there is no `kafka-compose.yaml`; #38 removed it). The noxfile
bakes in the required `SQUAREBOT_*` / `KAFKA_*` env vars and, on macOS +
Colima, auto-sets `TESTCONTAINERS_HOST_OVERRIDE`. pytest runs from the
repo root with `testpaths = ["tests"]` (the server suite), so posarg
paths are relative to the repo root.

The client suite is separate: `uv run --only-group=nox nox -s client_test`
runs `client/tests` in the workspace env. Run it when you touch `client/`.
(The multi-version `client_test_compat` / `client_test_oldest` sessions are
CI's responsibility, not the in-iteration gate.)

## Lint

- `lint_touched`: `uv run --only-group=lint pre-commit run --files {files}`
- `lint_all`: `uv run --only-group=nox nox -s lint`
  (equivalently `uv run --only-group=lint pre-commit run --all-files`)

Note: `pre-commit-uv` is intentionally omitted on Python 3.14 (its
uv-created hook venvs fail pre-commit's health check); plain `pre-commit`
on the virtualenv backend is used. Do not add `pre-commit-uv`.

## Typing

- `typing`: `uv run --only-group=nox nox -s typing`
  (mypy over `noxfile.py`, `src`, `tests`, and `client/src`)

## Final validation

End-of-task validation runs `uv run --only-group=nox nox -s lint`,
`... -s typing`, and `... -s test` in that order, in the foreground.
Docker must be running for the `test` session's testcontainers Kafka
broker. When you touched `client/`, also run `... -s client_test`. When
you touched `docs/`, also run `... -s docs` (Sphinx; the session sets the
import-time app env vars so OpenAPI generation works without a live
broker).

This is a two-package uv workspace, but the `test`/`lint`/`typing`
sessions already span both packages (mypy checks `src` and `client/src`;
lint runs over the whole tree). The Docker image build and the multi-
version PyPI `client` build are CI's responsibility, not the in-iteration
gate.

## Monorepo selectors

Routing is minimal: `lint`, `typing`, and the server `test` session run
through the same repo-root nox sessions regardless of which package you
changed. The one package-scoped session is `client_test` — run it (in
addition to the above) when you change `client/`.

## Quick reference: Makefile wrappers

The `Makefile` wraps the same commands for interactive use:
`make init` (sync `--all-groups` + install hooks), `make update-deps`
(`uv lock --upgrade` + `pre-commit autoupdate` + pin sync),
`make lint` / `make typing` / `make test` / `make run`.

<!-- stoker-onboarded-from: builtin:default
     prompt-hash: 348ec538f8f7f6fa42da3569d855eab629174668ef28ea225f8b37511daac9d4
     onboarded-at: 2026-06-18T19:30:53Z -->
