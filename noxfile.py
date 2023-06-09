import nox

# Default sessions
nox.options.sessions = ["lint", "typing"]

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
