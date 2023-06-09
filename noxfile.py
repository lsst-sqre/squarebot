import nox

# Default sessions
nox.options.sessions = ["lint", "typing", "test"]

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


@nox.session
def lint(session):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def typing(session):
    _install(session)
    session.install("mypy")
    with session.chdir("server"):
        session.run("mypy", "src", "tests", *session.posargs)
    with session.chdir("client"):
        session.run("mypy", "src", *session.posargs)


@nox.session
def test(session):
    _install(session)
    with session.chdir("server"):
        session.run(
            "pytest",
            "--cov=squarebot",
            "--cov-branch",
            *session.posargs,
            env={
                "SAFIR_LOG_LEVEL": "DEBUG",
                "SAFIR_ENVIRONMENT_URL": "http://example.org",
                "SQUAREBOT_REGISTRY_URL": "http://registry.example.org",
                "KAFKA_BOOTSTRAP_SERVERS": "http://broker.example.org",
                "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
                "SQUAREBOT_SLACK_SIGNING": "1234",
                "SQUAREBOT_SLACK_TOKEN": "1234",
                "SQUAREBOT_SLACK_APP_ID": "1234",
            },
        )
