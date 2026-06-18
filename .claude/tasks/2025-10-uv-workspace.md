# Migration to uv Workspaces

**Status:** Planning
**Created:** 2025-10-30
**Template Project:** [lsst-sqre/repertoire](https://github.com/lsst-sqre/repertoire)

## Overview

This document outlines the migration plan for converting Squarebot from a requirements.txt-based dependency management system to uv workspaces with modern Python packaging practices.

### Goals

1. **Adopt uv workspaces** - Leverage uv's workspace feature for managing the monorepo
2. **Replace requirements.txt with uv.lock** - Single lock file for all dependencies
3. **Use pyproject.toml dependency groups** - Organize dependencies by purpose (dev, docs, lint, typing, nox)
4. **Simplify noxfile.py** - Use nox-uv for cleaner session definitions
5. **Modernize Dockerfile** - Use uv for efficient container builds
6. **Update CI/CD** - Adapt GitHub Actions for uv-based workflows
7. **Update to Python 3.13+** - Adopt latest Python version and update dependencies (safir[kafka], etc.)

### Migration Strategy: Atomic Commits

This migration is organized around **atomic commits** - each commit leaves the project in a working, testable state. This approach:
- Makes the migration reversible at any point
- Enables easier code review
- Allows bisecting if issues are discovered later
- Provides clear checkpoints for validation

## Current State Analysis

### Project Structure

```
squarebot/
├── pyproject.toml              # Root config (ruff, mypy, scriv only)
├── noxfile.py                  # Custom install logic with pip/uv
├── server/                     # Main application
│   ├── pyproject.toml          # Package: squarebot, dependencies = []
│   ├── requirements/
│   │   ├── main.in             # 18 runtime dependencies
│   │   ├── main.txt            # ~139 pinned dependencies
│   │   ├── dev.in              # 21 dev dependencies
│   │   └── dev.txt             # ~406 pinned dependencies
│   └── src/squarebot/          # Application code
├── client/                     # Shared models library
│   ├── pyproject.toml          # Package: rubin-squarebot
│   └── src/rubin/squarebot/    # Pydantic models
└── docs/                       # Sphinx documentation
```

### Key Characteristics

- **Two packages**: `squarebot` (server, not published) and `rubin-squarebot` (client, published to PyPI)
- **Dependency management split**: Server uses requirements.txt, client uses pyproject.toml
- **Version management**: Both use setuptools_scm with `root = "../"`
- **Development workflow**: noxfile.py with custom `_install()` function
- **Build backend**: setuptools with setuptools_scm

## Target State (Based on Repertoire)

### Project Structure (Option A: Reorganize)

```
squarebot/
├── pyproject.toml              # Workspace root + squarebot package
├── uv.lock                     # Single lock file
├── noxfile.py                  # Simplified with nox-uv
├── Makefile                    # Common development commands
├── src/squarebot/              # Main application code (moved from server/src)
├── tests/                      # Tests (moved from server/tests)
├── client/                     # Shared models library
│   ├── pyproject.toml          # Package: rubin-squarebot
│   ├── src/rubin/squarebot/    # Pydantic models
│   └── tests/                  # Client tests (if any)
├── docs/                       # Sphinx documentation
└── scripts/                    # Build and utility scripts
```

### Project Structure (Option B: Keep Current Layout)

```
squarebot/
├── pyproject.toml              # Workspace root only
├── uv.lock                     # Single lock file
├── noxfile.py                  # Simplified with nox-uv
├── Makefile                    # Common development commands
├── server/                     # Main application
│   ├── pyproject.toml          # Package: squarebot (with dependencies)
│   ├── src/squarebot/          # Application code
│   └── tests/                  # Tests
├── client/                     # Shared models library
│   ├── pyproject.toml          # Package: rubin-squarebot
│   └── src/rubin/squarebot/    # Pydantic models
├── docs/                       # Sphinx documentation
└── scripts/                    # Build and utility scripts
```

### Dependency Groups (Standard Across Projects)

All pyproject.toml files should use these dependency groups:

- **`dev`** - Testing dependencies (pytest, coverage, httpx, asgi-lifespan, respx)
- **`docs`** - Documentation dependencies (documenteer, scriv, autodoc_pydantic)
- **`lint`** - Linting tools (ruff, pre-commit)
- **`typing`** - Type checking (mypy and type stubs)
- **`nox`** - Nox session runner

## Recommended Approach: Option A (Reorganize)

**Rationale:**
1. **Consistency with repertoire** - Makes it easier to maintain similar projects
2. **Simpler structure** - Root pyproject.toml contains the main package
3. **Clearer separation** - src/ for main app, client/ for library, tests/ at root
4. **Better for monorepos** - Standard practice for workspace-based projects
5. **Easier to reason about** - One main package at root, one workspace member

**Trade-offs:**
- Requires more file moves during migration
- May need to update import statements in tests
- CI/CD workflows need adjustments for new paths

## Migration Plan: Atomic Commits

### Commit 0: Preparation (Not Committed)

Before making any commits, complete these preparation tasks:

- [x] Study repertoire's uv workspace setup
- [x] Document current squarebot structure
- [x] Identify all dependency sources
- [ ] Create feature branch: `tickets/DM-51754`
- [ ] Ensure all tests pass on current main branch
- [ ] Document current behavior for comparison

#### Dependency Inventory

**From server/requirements/main.in (Runtime Dependencies):**
- fastapi
- starlette
- uvicorn[standard]
- python-multipart
- safir[kafka]>=5.0.0  (Note: Will update to >=14.1 for Python 3.13+ and faststream compatibility)
- pydantic-settings
- faststream[kafka]<0.5.0  (Note: Will relax to match safir's constraint: >=0.5.44,<0.6)
- (Plus transitive dependencies in main.txt)

**From server/requirements/dev.in (Development Dependencies):**
- asgi-lifespan
- coverage[toml]
- httpx
- mypy
- pre-commit
- pytest
- pytest-asyncio
- pytest-cov
- documenteer[guide]>=1,<2
- autodoc_pydantic
- scriv

**From client/pyproject.toml:**
- pydantic>=2
- safir

**Action Items:**
- [x] Check safir version for Python 3.13+ compatibility - **safir 14.1.0** confirmed compatible
- [x] Check faststream constraint - Use `faststream>=0.5.44,<0.6` to match safir[kafka] 14.1.0
- [ ] Verify all other dependencies support Python 3.13+

---

### Commit 1: Update Python version requirement to 3.13+

**Objective:** Update all Python version requirements to 3.13+, add .python-version file, and update CI to test on Python 3.13 and 3.14.

**Why this is atomic:** This commit only changes metadata and CI configuration. Tests continue to use the existing dependency management system and should pass on Python 3.13+.

**Changes:**
- [ ] Update `server/pyproject.toml`: `requires-python = ">=3.13"`
- [ ] Update `client/pyproject.toml`: `requires-python = ">=3.13"`
- [ ] Create `.python-version` file with content: `3.13`
- [ ] Update `.github/workflows/ci.yaml`:
  - Change Python version matrix to `["3.13", "3.14"]`
  - Update any hardcoded Python references
- [ ] Update `.github/workflows/periodic-ci.yaml` (if it has Python version references)
- [ ] Update `Dockerfile` to use `python:3.13-slim-bookworm` (or latest Debian base)

**Validation:**
- [ ] Run `nox` locally on Python 3.13 - all sessions should pass
- [ ] Commit with message: `Update Python version requirement to 3.13+`
- [ ] Push and verify CI passes

---

### Commit 2: Restructure directories to match repertoire layout

**Objective:** Move server code to root-level src/ and tests/ directories to match repertoire's structure.

**Why this is atomic:** All files move together with corresponding path updates. The old noxfile.py and GitHub Actions are updated to use new paths. Tests should pass using the existing requirements.txt system.

**Changes:**

**File Moves:**
- [ ] Create `src/` directory at root
- [ ] Move `server/src/squarebot/` → `src/squarebot/`
- [ ] Move `server/tests/` → `tests/`
- [ ] Create `scripts/` directory at root
- [ ] Move any scripts from `server/` to `scripts/` (if any exist)
- [ ] Delete empty `server/src/` and `server/tests/` directories
- [ ] Keep `server/` directory for now (contains pyproject.toml and requirements/)

**Path Updates:**
- [ ] Update `noxfile.py`:
  - Change all `with session.chdir("server"):` blocks
  - Update paths: `"server/src"` → `"src"`, `"server/tests"` → `"tests"`
  - Keep requirements paths as `"server/requirements/main.txt"` etc. (not moved yet)
- [ ] Update `.github/workflows/ci.yaml`:
  - Update any path references from `server/` to root
- [ ] Search codebase for hardcoded `"server/"` paths and update
- [ ] Check for relative imports in tests that might break

**Coverage Configuration:**
- [ ] Update root `pyproject.toml` (if it has coverage config): Update source paths
- [ ] Update `server/pyproject.toml` coverage config to point to `../src/squarebot`

**Validation:**
- [ ] Run `nox -s test` - tests should pass
- [ ] Run `nox -s typing` - type checking should pass
- [ ] Run `nox -s lint` - linting should pass
- [ ] Verify test discovery works correctly
- [ ] Commit with message: `Restructure directories to match repertoire layout`

---

### Commit 3: Migrate to uv workspaces and dependency groups

**Objective:** Replace requirements.txt system with uv workspaces, single uv.lock file, and pyproject.toml dependency groups. Rewrite noxfile.py to use nox-uv.

**Why this is atomic:** The dependency management system must be switched all at once. You cannot use both requirements.txt and uv.lock simultaneously in a consistent way. This commit includes all related changes: new pyproject.toml, uv.lock, updated noxfile.py, Makefile, and cleanup of old files.

**This is the largest commit but cannot be meaningfully split.**

#### 3.1 Create New Root pyproject.toml

- [ ] Create new `pyproject.toml` at root with:

```toml
[project]
name = "squarebot"
description = "SQuaRE Slack bot designed around Kafka microservice backends."
license = { file = "LICENSE" }
readme = "README.md"
keywords = ["rubin", "lsst"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Operating System :: POSIX",
    "Typing :: Typed",
]
requires-python = ">=3.13"
dependencies = [
    # Core FastAPI dependencies
    "fastapi>=0.100,<1",
    "starlette>=0.27,<1",
    "uvicorn[standard]>=0.30,<1",
    "python-multipart>=0.0.6,<1",

    # Rubin/SQuaRE dependencies
    "safir[kafka]>=14.1,<15",  # 14.1.0+ for Python 3.13+ and faststream >=0.5.44 compatibility
    "pydantic>=2.0,<3",
    "pydantic-settings>=2.0,<3",

    # Kafka/Streaming (constraint matches safir[kafka] 14.1.0 requirement)
    "faststream[kafka]>=0.5.44,<0.6",
    "aiokafka>=0.10,<1",

    # Client library (workspace member)
    "rubin-squarebot",
]
dynamic = ["version"]

[project.optional-dependencies]
dev = [
    # Testing
    "asgi-lifespan>=2.1,<3",
    "coverage[toml]>=7.6,<8",
    "httpx>=0.28,<1",
    "pytest>=8.3,<9",
    "pytest-asyncio>=0.24,<1",
    "pytest-cov>=6,<7",
]
docs = [
    "autodoc_pydantic>=2.2,<3",
    "documenteer[guide]>=2.3,<3",
    "scriv>=1.5,<2",
]
lint = [
    "pre-commit>=4,<5",
    "ruff>=0.12,<1",
]
typing = [
    "mypy>=1.15,<2",
    "types-PyYAML>=6,<7",
]
nox = [
    "nox>=2024.10,<2025",
    "nox-uv>=1,<2",
]

[project.scripts]
squarebot = "squarebot.cli:main"

[project.urls]
Homepage = "https://squarebot.lsst.io"
Source = "https://github.com/lsst-sqre/squarebot"

[build-system]
requires = ["setuptools>=61", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
# No root parameter needed - we're at the root

[tool.setuptools.packages.find]
where = ["src"]

[tool.uv.workspace]
members = ["client"]

[tool.uv.sources]
rubin-squarebot = { workspace = true }

# Tool configurations (moved from ruff-shared.toml and server/pyproject.toml)
[tool.ruff]
# Copy from ruff-shared.toml
line-length = 79  # Or whatever is in ruff-shared.toml
target-version = "py313"

[tool.ruff.lint]
# Copy from ruff-shared.toml

[tool.ruff.lint.extend-per-file-ignores]
# Merge from current root pyproject.toml
"noxfile.py" = ["D100", "T201"]
"src/squarebot/handlers/**" = ["D103", "B012"]
"tests/**" = ["C901", "D101", "D103", "PLR0915", "PT012", "S101", "S106", "SLF001"]

[tool.ruff.lint.isort]
known-first-party = ["squarebot", "rubin.squarebot", "tests"]
split-on-trailing-comma = false

[tool.mypy]
disallow_untyped_defs = true
disallow_incomplete_defs = true
ignore_missing_imports = true
local_partial_types = true
plugins = ["pydantic.mypy"]
no_implicit_reexport = true
show_error_codes = true
strict_equality = true
warn_redundant_casts = true
warn_unreachable = true
warn_unused_ignores = true

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
warn_untyped_fields = true

[tool.pytest.ini_options]
asyncio_mode = "strict"
python_files = ["tests/*.py", "tests/*/*.py"]

[tool.coverage.run]
parallel = true
branch = true
source = ["squarebot", "rubin.squarebot"]

[tool.coverage.paths]
source = ["src", "client/src", ".nox/*/lib/*/site-packages"]

[tool.coverage.report]
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.scriv]
categories = [
    "Backwards-incompatible changes",
    "New features",
    "Bug fixes",
    "Other changes",
]
entry_title_template = "{{ version }} ({{ date.strftime('%Y-%m-%d') }})"
format = "md"
md_header_level = "2"
new_fragment_template = "file:changelog.d/_template.md"
skip_fragments = "_template.md"
```

#### 3.2 Update Client pyproject.toml

- [ ] Update `client/pyproject.toml`:
  - Remove `root = "../"` from `[tool.setuptools_scm]` section
  - Keep dependencies as-is (pydantic>=2, safir)
  - Update requires-python to 3.13+ (already done in Commit 1, but verify)
  - Ensure it works as a workspace member

#### 3.3 Generate uv.lock

- [ ] Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Run: `uv lock`
- [ ] Verify `uv.lock` is created and includes both packages
- [ ] Run: `uv sync --all-groups` to test installation
- [ ] Verify both squarebot and rubin-squarebot are installed

#### 3.4 Rewrite noxfile.py for nox-uv

- [ ] Replace entire `noxfile.py` with nox-uv version:

```python
"""Nox sessions for testing, linting, and documentation."""

import nox

# Default sessions to run
nox.options.sessions = ["lint", "typing", "test", "docs"]

# Use uv for virtual environment management
nox.options.default_venv_backend = "uv|virtualenv"


def _make_env_vars() -> dict[str, str]:
    """Create environment variables for test sessions."""
    return {
        "SQUAREBOT_LOG_LEVEL": "DEBUG",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "SQUAREBOT_SLACK_SIGNING": "1234",
        "SQUAREBOT_SLACK_TOKEN": "1234",
        "SQUAREBOT_SLACK_APP_ID": "1234",
    }


@nox.session
def lint(session: nox.Session) -> None:
    """Run pre-commit hooks."""
    # Use only lint group, don't install the project
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--no-install-project",
        "--only-group",
        "lint",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def typing(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--only-group",
        "typing",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("mypy", "noxfile.py")
    session.run("mypy", "src", "tests", *session.posargs)
    # Type check client
    with session.chdir("client"):
        session.run("mypy", "src", *session.posargs)


@nox.session
def test(session: nox.Session) -> None:
    """Run pytest with coverage."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--group",
        "dev",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run(
        "pytest",
        "--cov=squarebot",
        "--cov=rubin.squarebot",
        "--cov-branch",
        "--cov-report=",
        *session.posargs,
        env=_make_env_vars(),
    )


@nox.session
def coverage_report(session: nox.Session) -> None:
    """Generate coverage report."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--only-group",
        "dev",
        "--no-install-project",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("coverage", "report")


@nox.session
def docs(session: nox.Session) -> None:
    """Build documentation."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--group",
        "docs",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    doctree_dir = str((session.cache_dir / "doctrees").absolute())
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "--keep-going",
            "-n",
            "-T",
            "-b",
            "html",
            "-d",
            doctree_dir,
            ".",
            "./_build/html",
            env=_make_env_vars(),
        )


@nox.session(name="docs-clean")
def docs_clean(session: nox.Session) -> None:
    """Build documentation from scratch."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--group",
        "docs",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    with session.chdir("docs"):
        session.run("rm", "-rf", "_build", external=True)
    doctree_dir = str((session.cache_dir / "doctrees").absolute())
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "--keep-going",
            "-n",
            "-T",
            "-b",
            "html",
            "-d",
            doctree_dir,
            ".",
            "./_build/html",
            env=_make_env_vars(),
        )


@nox.session(name="docs-linkcheck")
def docs_linkcheck(session: nox.Session) -> None:
    """Check documentation links."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--group",
        "docs",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    doctree_dir = str((session.cache_dir / "doctrees").absolute())
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "--keep-going",
            "-n",
            "-T",
            "-b",
            "linkcheck",
            "-d",
            doctree_dir,
            ".",
            "./_build/html",
            env=_make_env_vars(),
        )


@nox.session(name="scriv-create")
def scriv_create(session: nox.Session) -> None:
    """Create a changelog fragment."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--only-group",
        "docs",
        "--no-install-project",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("scriv", "create")


@nox.session(name="scriv-collect")
def scriv_collect(session: nox.Session) -> None:
    """Collect changelog fragments."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--only-group",
        "docs",
        "--no-install-project",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("scriv", "collect", "--add", "--version", *session.posargs)


@nox.session(name="run")
def run(session: nox.Session) -> None:
    """Run the application in development mode."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run(
        "uvicorn",
        "squarebot.main:app",
        "--reload",
        env=_make_env_vars(),
    )
```

#### 3.5 Create Makefile

- [ ] Create `Makefile` at root:

```makefile
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make init         - Set up development environment"
	@echo "  make update       - Update dependencies and reinitialize"
	@echo "  make update-deps  - Update uv.lock and pre-commit hooks"

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
```

#### 3.6 Create scripts/update-uv-version.sh

- [ ] Create `scripts/update-uv-version.sh` (copy and adapt from repertoire)
- [ ] Make it executable: `chmod +x scripts/update-uv-version.sh`

#### 3.7 Delete Old Files

- [ ] Delete `server/pyproject.toml`
- [ ] Delete entire `server/requirements/` directory
- [ ] Delete `ruff-shared.toml`
- [ ] Delete empty `server/` directory if it now only contains deleted files
- [ ] Update any `.gitignore` rules that referenced these files

#### 3.8 Update .pre-commit-config.yaml

- [ ] Pin uv version in `.pre-commit-config.yaml` if there's a uv hook
- [ ] Update any paths if needed

**Validation:**
- [ ] Run `make init` - should set up environment
- [ ] Run `nox` - all sessions should pass
- [ ] Run `nox -s test` - tests should pass with coverage
- [ ] Run `nox -s typing` - type checking should pass
- [ ] Run `nox -s lint` - linting should pass
- [ ] Run `nox -s docs` - docs should build
- [ ] Verify no imports broke
- [ ] Commit with message: `Migrate to uv workspaces and dependency groups`

---

### Commit 4: Update Dockerfile for uv

**Objective:** Modernize Dockerfile to use uv for dependency installation, following repertoire's pattern.

**Why this is atomic:** Docker build process is independent of local development. This commit only changes how the container image is built.

**Changes:**
- [ ] Update `Dockerfile`:

```dockerfile
# Base image
FROM python:3.13-slim-bookworm AS base-image

# Run install script for system packages
COPY scripts/install-base-packages.sh .
RUN ./install-base-packages.sh && rm install-base-packages.sh

# Install stage
FROM base-image AS install

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /usr/local/bin/

# Set uv environment variables
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Set working directory
WORKDIR /workdir

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY client/pyproject.toml ./client/

# Install dependencies (production only)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Runtime stage
FROM base-image AS runtime-image

# Create non-root user
RUN useradd -m -d /home/appuser -s /bin/bash appuser

# Copy virtualenv from install stage
COPY --from=install /workdir/.venv /opt/venv

# Set PATH to use virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "squarebot.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] Update `scripts/install-base-packages.sh` if needed for Python 3.13
- [ ] Remove `scripts/install-dependency-packages.sh` if it exists (no longer needed)

**Validation:**
- [ ] Build Docker image: `docker build -t squarebot:test .`
- [ ] Verify build succeeds
- [ ] Check image size (compare to previous)
- [ ] Test running the container locally (requires Kafka)
- [ ] Commit with message: `Update Dockerfile to use uv for dependency management`

---

### Commit 5: Update GitHub Actions for uv

**Objective:** Update CI/CD workflows to use uv via the setup-uv action, update caching strategy, and use new development commands.

**Why this is atomic:** CI/CD configuration is independent and can be updated as a unit.

**Changes:**

**Update .github/workflows/ci.yaml:**
- [ ] Add uv installation step to all jobs that need it
- [ ] Update test job:

```yaml
test:
  runs-on: ubuntu-latest
  timeout-minutes: 10
  strategy:
    matrix:
      python:
        - "3.13"
        - "3.14"
  steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v5
      with:
        version: "0.9.3"
        enable-cache: true
        cache-dependency-glob: "uv.lock"

    - name: Set up Python
      run: uv python install ${{ matrix.python }}

    - name: Start Kafka
      run: docker compose -f kafka-compose.yaml up -d

    - name: Run nox
      run: uvx --with nox --with nox-uv nox -s lint typing test

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
```

- [ ] Update docs job similarly (add uv setup, use uvx nox)
- [ ] Update any other jobs that run Python code
- [ ] Remove any pip/requirements.txt references
- [ ] Update cache keys to use `uv.lock` instead of `**/pyproject.toml`

**Update .github/workflows/periodic-ci.yaml:**
- [ ] Add uv setup
- [ ] Change dependency update command from `nox -s update-deps` to `make update-deps`
- [ ] Ensure it commits and pushes `uv.lock` changes

**Validation:**
- [ ] Push to feature branch
- [ ] Verify all CI jobs pass
- [ ] Check that caching works (should see cache hits on second run)
- [ ] Verify build times (should be similar or faster)
- [ ] Commit with message: `Update GitHub Actions to use uv`

---

### Commit 6: Update documentation

**Objective:** Update all documentation to reflect the new uv-based workflow.

**Why this is atomic:** Documentation updates don't affect functionality and can be done as a final cleanup commit.

**Changes:**

**Update CLAUDE.md:**
- [ ] Update "Development Commands" section:
  ```markdown
  ### Setup

  \`\`\`bash
  # Install uv if needed
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Set up development environment
  make init

  # Or manually:
  uv sync --frozen --all-groups
  uv run pre-commit install
  \`\`\`
  ```
- [ ] Update "Testing and Quality" section - use `uvx nox` instead of `nox`
- [ ] Update "Dependency Management" section:
  ```markdown
  ### Dependency Management

  \`\`\`bash
  # Update dependencies and pre-commit hooks
  make update-deps

  # Refresh your environment
  make init
  \`\`\`

  Dependencies are defined in `pyproject.toml` dependency groups and locked in `uv.lock`.
  ```
- [ ] Update Docker build section to mention uv
- [ ] Update Python version requirement to 3.13+
- [ ] Remove references to requirements.txt files
- [ ] Update dependency groups section

**Update README.md:**
- [ ] Update installation instructions
- [ ] Update development setup section
- [ ] Add uv requirement
- [ ] Update Python version to 3.13+
- [ ] Update any command examples

**Update docs/ (if needed):**
- [ ] Update developer guides with new workflow
- [ ] Update any architecture docs mentioning dependency management
- [ ] Update build/deployment docs

**Create Changelog Entry:**
- [ ] Run: `uvx --with nox --with nox-uv nox -s scriv-create`
- [ ] Edit the changelog fragment in `changelog.d/`:
  ```markdown
  ### Backwards-incompatible changes

  - Squarebot now requires Python 3.13 or later.
  - Development workflow now uses uv for dependency management. Run `make init` to set up your development environment.

  ### New features

  - Migrated to uv workspaces for dependency management with a single `uv.lock` file.
  - Added Makefile with common development commands (`make init`, `make update`, `make update-deps`).
  - Reorganized repository structure: server code is now in `src/squarebot/` and tests are in `tests/` at the repository root.
  - Updated noxfile.py to use nox-uv for cleaner session definitions.
  - Modernized Dockerfile to use uv for efficient container builds.

  ### Other changes

  - Updated all dependencies to versions compatible with Python 3.13+.
  - Consolidated configuration: removed `server/requirements/` directory and `ruff-shared.toml`.
  - Dependencies are now organized into groups (dev, docs, lint, typing, nox) in `pyproject.toml`.
  ```

**Validation:**
- [ ] Build docs: `uvx --with nox --with nox-uv nox -s docs`
- [ ] Verify docs build successfully
- [ ] Check that all links work
- [ ] Review README and CLAUDE.md for accuracy
- [ ] Commit with message: `Update documentation for uv workspace migration`

---

### Post-Migration Tasks

After all commits are made and pushed:

- [ ] Create pull request with comprehensive description
- [ ] Add before/after comparison (directory structure, setup commands, etc.)
- [ ] Request review
- [ ] Ensure all CI checks pass
- [ ] Test fresh clone: `git clone && cd squarebot && make init && uvx --with nox --with nox-uv nox`
- [ ] Merge PR
- [ ] Tag new version (if appropriate)
- [ ] Monitor for any issues
- [ ] Update any external documentation (wikis, team docs, etc.)


## Open Questions and Decisions

### 1. Python Version Requirement ✅ DECIDED
**Decision:** Target Python 3.13+ (per user requirement)

**Rationale:**
- Latest stable Python version
- User explicitly requested 3.13+
- Provides modern features and performance improvements
- Aligns with pushing projects forward

**Impact:**
- Need to verify all dependencies support Python 3.13+
- Need to update safir version (likely >=6.0 for Python 3.13+ support)
- Need to update GitHub Actions to test on 3.13 and 3.14

### 2. Directory Structure ✅ DECIDED
**Decision:** Reorganize to match repertoire layout (Option A)

**Rationale:**
- Consistency with other SQuaRE projects
- Cleaner workspace structure
- Standard monorepo layout
- One-time migration cost worth long-term maintainability

**Changes:**
- `server/src/squarebot/` → `src/squarebot/`
- `server/tests/` → `tests/`
- Root `pyproject.toml` contains main package

### 3. Workspace Strategy ✅ DECIDED
**Decision:** Use workspace members (client as workspace member)

**Rationale:**
- Follows repertoire pattern
- Allows separate versioning and publishing
- Client can be installed independently
- Better dependency resolution

### 4. safir Version and Extras ✅ CONFIRMED
**Decision:** Use `safir[kafka]>=14.1,<15` (per user confirmation)

**Notes:**
- Current constraint: `safir[kafka]>=5.0.0`
- Updating to: `safir[kafka]>=14.1,<15`
- safir 14.1.0 confirmed compatible with Python 3.13+
- safir[kafka] extra provides kafka dependencies compatible with safir

### 5. faststream Version ✅ DECIDED
**Decision:** Relax to `faststream[kafka]>=0.5.44,<0.6` to match safir[kafka] constraint

**Rationale:**
- safir 14.1.0 has dependency: `faststream>=0.5.44,<0.6`
- Must be compatible with safir[kafka]
- Relaxing from current `<0.5.0` constraint to `>=0.5.44,<0.6`

**Current State:** `faststream[kafka]<0.5.0` in requirements/main.in
**New State:** `faststream[kafka]>=0.5.44,<0.6` (matches safir's requirement)

##Risk Assessment

### High Risk
1. **Dependency compatibility** - Some dependencies may not yet support Python 3.13
   - Mitigation: Check each dependency before starting, have fallback versions ready
2. **Import path changes (Commit 2)** - File moves could break imports
   - Mitigation: Thorough testing after Commit 2, search for hardcoded paths
3. **Dependency resolution changes (Commit 3)** - uv may resolve differently than pip
   - Mitigation: Careful review of uv.lock, test all functionality

### Medium Risk
1. **CI/CD disruption (Commit 5)** - GitHub Actions changes could cause deployment issues
   - Mitigation: Test in feature branch first, have rollback plan
2. **Docker build changes (Commit 4)** - New build process needs validation
   - Mitigation: Test locally before pushing, compare image sizes
3. **noxfile.py rewrite (Commit 3)** - New patterns may have subtle differences
   - Mitigation: Run all nox sessions locally before committing

### Low Risk
1. **Documentation updates (Commit 6)** - Can be fixed post-migration
2. **Makefile addition** - Optional convenience, doesn't break anything
3. **Pre-commit hooks** - Easy to fix if issues arise

## Success Criteria

After migration is complete, the following must all be true:

### Functionality
- [ ] All nox sessions pass locally (`uvx --with nox --with nox-uv nox`)
- [ ] All GitHub Actions CI jobs pass
- [ ] Docker image builds successfully
- [ ] Application starts and runs correctly
- [ ] Tests pass with same or better coverage
- [ ] Type checking passes with no new errors
- [ ] Linting passes with no new errors

### Publishability
- [ ] PyPI publishing works for client package (`rubin-squarebot`)
- [ ] Version management via setuptools_scm works correctly
- [ ] Client package can be installed independently

### Documentation
- [ ] README reflects new setup process
- [ ] CLAUDE.md updated with new commands
- [ ] Changelog entry created
- [ ] All docs build successfully

### Developer Experience
- [ ] `make init` sets up development environment from scratch
- [ ] `make update` updates all dependencies
- [ ] New developers can follow README to get started
- [ ] No breaking changes for downstream consumers of `rubin-squarebot`

## Timeline Estimate

Based on atomic commits:

- **Commit 0 (Preparation):** 1-2 hours
- **Commit 1 (Python 3.13+):** 1-2 hours
- **Commit 2 (Directory restructure):** 2-3 hours
- **Commit 3 (uv migration):** 6-8 hours (largest commit)
- **Commit 4 (Dockerfile):** 2-3 hours
- **Commit 5 (GitHub Actions):** 2-3 hours
- **Commit 6 (Documentation):** 2-3 hours
- **Post-migration validation:** 2-3 hours

**Total Estimated Time:** 18-27 hours

**Note:** Commit 3 is the most time-consuming because it involves:
- Creating comprehensive new pyproject.toml
- Mapping all dependencies from requirements.txt
- Generating and validating uv.lock
- Complete noxfile.py rewrite
- Testing all nox sessions work with new setup

## References

- [uv Documentation - Workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [uv Documentation - Dockerfile Guide](https://docs.astral.sh/uv/guides/docker/)
- [Repertoire Repository](https://github.com/lsst-sqre/repertoire) (template project)
- [nox-uv Documentation](https://pypi.org/project/nox-uv/)
- [Python 3.13 Release Notes](https://docs.python.org/3/whatsnew/3.13.html)

## Notes and Lessons Learned

(To be filled in during migration)

### Dependency Compatibility Issues
- Record any dependencies that don't support Python 3.13+ yet
- Document any version constraints that needed adjustment

### Unexpected Challenges
- Any import issues that arose
- Any uv-specific behaviors different from pip
- Any nox-uv patterns that needed adjustment

### Performance Improvements
- Docker build time comparison (before/after)
- CI build time comparison
- Local development experience improvements

---

**End of Migration Plan**
