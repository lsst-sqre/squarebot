from __future__ import annotations

import json
import logging
import os
import re
import subprocess

import nox
from nox_uv import session

# Default sessions
nox.options.sessions = ["lint", "typing", "test", "client_test"]

# Other nox defaults
nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


def _setup_testcontainers_logging() -> None:
    """Configure logging to reduce testcontainers noise."""
    logging.getLogger("testcontainers").setLevel(logging.ERROR)
    logging.getLogger("docker").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


def _setup_testcontainers_env() -> None:
    """Configure testcontainers environment variables for Colima on macOS.

    This must be called before any containers are started to ensure the
    Reaper can connect properly when using Colima as the Docker runtime.
    """
    # Set testcontainers host override for Colima on macOS. This fixes
    # "nodename nor servname provided, or not known" errors.
    docker_host = os.getenv("DOCKER_HOST", "")
    m = re.search(r"\.colima/(?P<profile>[^/]+)/docker\.sock$", docker_host)
    if m:
        # Extract the Colima VM IP address for the active profile.
        # colima ls -j emits one JSON object per line (one per profile).
        try:
            result = subprocess.run(
                ["colima", "ls", "-j"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                colima_info = json.loads(line)
                if colima_info.get("name") == m["profile"] and colima_info.get(
                    "address"
                ):
                    os.environ["TESTCONTAINERS_HOST_OVERRIDE"] = colima_info[
                        "address"
                    ]
                    break
        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            KeyError,
        ):
            # If we can't get the Colima address, don't set the override.
            pass


def _make_env_vars(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Create an environment variable dictionary that lets the app start up.

    ``config`` and ``kafka_router`` are built at import time, so these must be
    set in the pytest subprocess environment before squarebot is imported.
    """
    env_vars = {
        "SQUAREBOT_LOG_LEVEL": "DEBUG",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "SQUAREBOT_SLACK_SIGNING": "1234",
        "SQUAREBOT_SLACK_TOKEN": "1234",
        "SQUAREBOT_SLACK_APP_ID": "1234",
    }
    if overrides:
        env_vars.update(overrides)
    return env_vars


@session(uv_only_groups=["lint"], uv_no_install_project=True)
def lint(session: nox.Session) -> None:
    """Run pre-commit hooks."""
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@session(uv_groups=["typing", "dev"])
def typing(session: nox.Session) -> None:
    """Run mypy."""
    session.run(
        "mypy",
        "noxfile.py",
        "src",
        "tests",
        "client/src",
        *session.posargs,
    )


@session(uv_groups=["dev"])
def test(session: nox.Session) -> None:
    """Run the server test suite against a testcontainers Kafka broker."""
    _setup_testcontainers_logging()
    _setup_testcontainers_env()

    # Import after setting environment variables so config is read correctly.
    from testcontainers.kafka import KafkaContainer  # noqa: PLC0415

    with KafkaContainer().with_kraft() as kafka:
        env_vars = _make_env_vars(
            {"KAFKA_BOOTSTRAP_SERVERS": kafka.get_bootstrap_server()}
        )
        session.run(
            "pytest",
            "--cov=squarebot",
            "--cov-branch",
            *session.posargs,
            env=env_vars,
        )


@session(uv_groups=["dev"])
def client_test(session: nox.Session) -> None:
    """Run the client test suite in the workspace environment."""
    session.run("pytest", "client/tests", *session.posargs)


@nox.session(name="client_test_compat", python=["3.13", "3.14"])
def client_test_compat(session: nox.Session) -> None:
    """Test the client against its supported Python versions."""
    session.install("-e", "./client", "pytest")
    session.run("pytest", "client/tests", *session.posargs)


@nox.session(name="client_test_oldest", python=["3.13"])
def client_test_oldest(session: nox.Session) -> None:
    """Test the client with the oldest supported direct dependencies."""
    session.install(
        "-e",
        "./client",
        "pytest>=8",
        env={"UV_RESOLUTION": "lowest-direct"},
    )
    session.run("pytest", "client/tests", *session.posargs)


@session(uv_groups=["docs"])
def docs(session: nox.Session) -> None:
    """Build the docs.

    ``squarebot.main:create_openapi`` imports the app (but does not start the
    lifespan), so the app config env vars must be present; no live broker is
    required.
    """
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "--keep-going",
            "-n",
            "-T",
            "-b",
            "html",
            "-d",
            str(doctree_dir),
            ".",
            "./_build/html",
            env=_make_env_vars(),
        )


@session(name="docs-linkcheck", uv_groups=["docs"])
def docs_linkcheck(session: nox.Session) -> None:
    """Linkcheck the docs."""
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "--keep-going",
            "-n",
            "-T",
            "-b",
            "linkcheck",
            "-d",
            str(doctree_dir),
            ".",
            "./_build/html",
            env=_make_env_vars(),
        )


@nox.session(name="scriv-create")
def scriv_create(session: nox.Session) -> None:
    """Create a scriv entry."""
    session.install("scriv")
    session.run("scriv", "create")


@nox.session(name="scriv-collect")
def scriv_collect(session: nox.Session) -> None:
    """Collect scriv entries."""
    session.install("scriv")
    session.run("scriv", "collect", "--add", "--version", *session.posargs)


@session(uv_groups=["dev"], name="run")
def run(session: nox.Session) -> None:
    """Run the application in development mode with a Kafka container."""
    _setup_testcontainers_logging()
    _setup_testcontainers_env()

    # Import after setting environment variables so config is read correctly.
    from testcontainers.kafka import KafkaContainer  # noqa: PLC0415

    with KafkaContainer().with_kraft() as kafka:
        env_vars = _make_env_vars(
            {"KAFKA_BOOTSTRAP_SERVERS": kafka.get_bootstrap_server()}
        )
        session.run(
            "uvicorn",
            "squarebot.main:app",
            "--reload",
            env=env_vars,
        )
