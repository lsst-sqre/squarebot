import nox

# Default sessions
nox.options.sessions = ["lint", "typing", "test", "docs"]

# Other nox defaults
nox.options.default_venv_backend = "venv"
nox.options.reuse_existing_virtualenvs = True


def _install(session, *args, **kwargs):
    """Install the application and all dependencies."""
    session.install("--upgrade", "pip", "setuptools", "wheel")
    session.install("-r", "server/requirements/main.txt")
    session.install("-r", "server/requirements/dev.txt")
    session.install("-e", "client")
    session.install("-e", "server")


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
            "-b" "html",
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
