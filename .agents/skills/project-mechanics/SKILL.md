---
name: project-mechanics
description: Project-specific build/test/lint/typing commands for this repo. Read this skill at the start of any phase that runs validation (`stoker-work`, `stoker-fixup`, `stoker-rebase`).
---

# Project mechanics

This file is the source of truth for how this repo runs tests, lint,
and type-checking. Profile-shipped phase skills read it at the start
of each phase and use the named commands verbatim.

## Test commands

- `focused_test`: `nox -s test -- <pytest args>` (e.g. `nox -s test -- tests/handlers/foo_test.py::test_bar`)
- `complete_test`: `nox -s test`

Both require a running Kafka broker — start it first with
`docker compose -f kafka-compose.yaml up -d`. `nox` bakes in the
required `SQUAREBOT_*` / `KAFKA_*` env vars, and runs pytest from
`server/`, so posarg paths are relative to `server/` (the server
suite also covers the `client` package).

## Lint

- `lint_touched`: `pre-commit run --files {files}`
- `lint_all`: `nox -s lint`

## Typing

- `typing`: `nox -s typing`

## Final validation

End-of-task validation runs `nox -s test` + `nox -s lint` +
`nox -s typing` in that order, in the foreground. Bring up the Kafka
broker first with `docker compose -f kafka-compose.yaml up -d`, since
the test gate needs it.

This is a two-package monorepo (`client/` + `server/`), but the nox
sessions span both packages in a single pass, so `complete_test` is
not package-scoped — `nox -s test` runs the unified `server/` suite
(which also exercises the `client` package) and `nox -s typing` mypies
the noxfile, `server`, and `client` together. There is no multi-version
matrix; the Docker image build and the PyPI `client` package build are
CI's responsibility, not the in-iteration gate.

Plus `nox -s docs` (Sphinx) when `docs/` is touched.

## Monorepo selectors

This repo is a monorepo (`client/` + `server/`), but there is no
per-package command routing: every validation command above goes
through the same repo-root nox sessions, which already cover both
packages. Run the same `focused_test` / `complete_test` / `lint_*` /
`typing` commands regardless of which package you changed.

<!-- stoker-onboarded-from: builtin:default
     prompt-hash: 348ec538f8f7f6fa42da3569d855eab629174668ef28ea225f8b37511daac9d4
     onboarded-at: 2026-06-18T19:30:53Z -->
