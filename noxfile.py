import nox

# Default sessions
nox.options.sessions = ["lint", "typing", "test", "docs"]

# Other nox defaults
nox.options.default_venv_backend = "venv"
nox.options.reuse_existing_virtualenvs = True


# Pip install dependencies for the client and server packages
dependencies = [
    ("--upgrade", "pip", "setuptools", "wheel"),
    ("-r", "server/requirements/main.txt"),
    ("-r", "server/requirements/dev.txt"),
    ("-e", "client"),
    ("-e", "server"),
]


def _install(session):
    """Install the application and all dependencies into the session."""
    for deps in dependencies:
        session.install(*deps)


def _make_env_vars():
    """Create a environment variable dictionary for test sessions that enables
    the app to start up.
    """
    return {
        "SAFIR_LOG_LEVEL": "DEBUG",
        "SAFIR_ENVIRONMENT_URL": "http://example.org",
        "SQUAREBOT_REGISTRY_URL": "http://registry.example.org",
        "KAFKA_BOOTSTRAP_SERVERS": "http://broker.example.org",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "SQUAREBOT_SLACK_SIGNING": "1234",
        "SQUAREBOT_SLACK_TOKEN": "1234",
        "SQUAREBOT_SLACK_APP_ID": "1234",
    }


@nox.session
def lint(session):
    """Run pre-commit hooks."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def typing(session):
    """Run mypy."""
    _install(session)
    session.install("mypy")
    with session.chdir("server"):
        session.run("mypy", "src", "tests", *session.posargs)
    with session.chdir("client"):
        session.run("mypy", "src", *session.posargs)


@nox.session
def test(session):
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
def docs(session):
    """Build the docs."""
    _install(session)
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "-W",
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
def docs_linkcheck(session):
    """Linkcheck the docs."""
    _install(session)
    doctree_dir = (session.cache_dir / "doctrees").absolute()
    with session.chdir("docs"):
        session.run(
            "sphinx-build",
            "-W",
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
def scriv_create(session):
    """Create a scriv entry."""
    session.install("scriv")
    session.run("scriv", "create")


@nox.session(name="scriv-collect")
def scriv_collect(session):
    """Collect scriv entries."""
    session.install("scriv")
    session.run("scriv", "collect", "--add", "--version", *session.posargs)


@nox.session(name="update-deps")
def update_deps(session):
    """Update pinned server dependencies and pre-commit hooks."""
    session.install(
        "--upgrade", "pip-tools", "pip", "setuptools", "wheel", "pre-commit"
    )
    session.run("pre-commit", "autoupdate")

    # Dependencies are unpinned for compatibility with the unpinned client
    # dependency.
    session.run(
        "pip-compile",
        "--upgrade",
        "--build-isolation",
        "--allow-unsafe",
        "--output-file",
        "server/requirements/main.txt",
        "server/requirements/main.in",
    )

    session.run(
        "pip-compile",
        "--upgrade",
        "--build-isolation",
        "--allow-unsafe",
        "--output-file",
        "server/requirements/dev.txt",
        "server/requirements/dev.in",
    )

    print("\nTo refresh the development venv, run:\n\n\tnox -s dev-init\n")


@nox.session(name="dev-init")
def init_dev(session):
    """Set up a development venv."""
    # Create a venv in the current directory, replacing any existing one
    session.run("python", "-m", "venv", ".venv", "--clear")
    # Install the dependencies into this venv by running pip from the venv.
    python = ".venv/bin/python"
    for deps in dependencies:
        session.run(python, "-m", "pip", "install", *deps, external=True)
    session.run(
        python, "-m", "pip", "install", "nox", "pre-commit", external=True
    )

    print(
        "\nTo activate this virtual env, run:\n\n\tsource .venv/bin/activate\n"
    )


@nox.session(name="run")
def run(session):
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
