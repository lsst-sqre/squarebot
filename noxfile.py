import nox

# Default sessions
nox.options.sessions = ["lint", "typing", "test", "docs"]

# Other nox defaults
nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


# Pip installable dependencies for the client and server packages
PIP_DEPENDENCIES = [
    ("-r", "server/requirements/main.txt"),
    ("-r", "server/requirements/dev.txt"),
    ("-e", "client"),
    ("-e", "server"),
]


def _install(session: nox.Session) -> None:
    """Install the application and all dependencies into the session."""
    session.install("--upgrade", "uv")
    for deps in PIP_DEPENDENCIES:
        session.install(*deps)


def _install_dev(session: nox.Session, bin_prefix: str = "") -> None:
    """Install the application and all development dependencies into the
    specified virtual environment.
    """
    python = f"{bin_prefix}python"
    precommit = f"{bin_prefix}pre-commit"

    # Install dev dependencies
    session.run(python, "-m", "pip", "install", "uv", external=True)
    for deps in PIP_DEPENDENCIES:
        session.run(python, "-m", "uv", "pip", "install", *deps, external=True)
    session.run(
        python,
        "-m",
        "uv",
        "pip",
        "install",
        "nox",
        "pre-commit",
        external=True,
    )
    # Install pre-commit hooks
    session.run(precommit, "install", external=True)


def _make_env_vars() -> dict[str, str]:
    """Create a environment variable dictionary for test sessions that enables
    the app to start up.
    """
    return {
        "SQUAREBOT_LOG_LEVEL": "DEBUG",
        "SQUAREBOT_ENVIRONMENT_URL": "http://example.org",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "SQUAREBOT_SLACK_SIGNING": "1234",
        "SQUAREBOT_SLACK_TOKEN": "1234",
        "SQUAREBOT_SLACK_APP_ID": "1234",
    }


@nox.session(name="venv-init")
def init_dev(session: nox.Session) -> None:
    """Set up a development venv."""
    # Create a venv in the current directory, replacing any existing one
    session.run("python", "-m", "venv", ".venv", "--clear")
    _install_dev(session, bin_prefix=".venv/bin/")

    print(
        "\nTo activate this virtual env, run:\n\n\tsource .venv/bin/activate\n"
    )


@nox.session(name="init", python=False)
def init(session: nox.Session) -> None:
    """Set up the development environment in the current virtual env."""
    _install_dev(session, bin_prefix="")


@nox.session
def lint(session: nox.Session) -> None:
    """Run pre-commit hooks."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def typing(session: nox.Session) -> None:
    """Run mypy."""
    _install(session)
    session.install("mypy")
    session.run("mypy", "noxfile.py")
    with session.chdir("server"):
        session.run("mypy", "src", "tests", *session.posargs)
    with session.chdir("client"):
        session.run("mypy", "src", *session.posargs)


@nox.session
def test(session: nox.Session) -> None:
    """Run pytest."""
    _install(session)
    with session.chdir("server"):
        session.run(
            "pytest",
            "--cov=squarebot",
            "--cov-branch",
            *session.posargs,
            env=_make_env_vars(),
        )


@nox.session
def docs(session: nox.Session) -> None:
    """Build the docs."""
    _install(session)
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            # "-W",
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


@nox.session(name="docs-linkcheck")
def docs_linkcheck(session: nox.Session) -> None:
    """Linkcheck the docs."""
    _install(session)
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            # "-W",
            "--keep-going",
            "-n",
            "-T",
            "-b" "linkcheck",
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


@nox.session(name="update-deps")
def update_deps(session: nox.Session) -> None:
    """Update pinned server dependencies and pre-commit hooks."""
    session.install(
        "--upgrade", "pip-tools", "pip", "setuptools", "wheel", "pre-commit"
    )
    session.run("pre-commit", "autoupdate")

    # Dependencies are unpinned for compatibility with the unpinned client
    # dependency.
    session.run(
        "uv",
        "pip",
        "compile",
        "--upgrade",
        "--output-file",
        "server/requirements/main.txt",
        "server/requirements/main.in",
    )

    session.run(
        "uv",
        "pip",
        "compile",
        "--upgrade",
        "--output-file",
        "server/requirements/dev.txt",
        "server/requirements/dev.in",
    )

    print("\nTo refresh the development venv, run:\n\n\tnox -s init\n")


@nox.session(name="run")
def run(session: nox.Session) -> None:
    """Run the application in development mode."""
    # Note this doesn't work right now because Kafka is needed for the app.
    _install(session)
    with session.chdir("server"):
        session.run(
            "uvicorn",
            "squarebot.main:app",
            "--reload",
            env=_make_env_vars(),
        )
