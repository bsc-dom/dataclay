import nox

# Define which Python versions to test with
PYPROJECT = nox.project.load_toml("pyproject.toml")
PYTHON_VERSIONS = nox.project.python_versions(PYPROJECT)
DEFAULT_PYTHON = "3.10"  # Modern-ish version compatible with the legacy-deps

# Default sessions (these will be executed in Github Actions)
# Maintain a clear separation between code checking and code altering tasks (don't add format)
nox.options.sessions = ["lint", "protos", "tests"]
# nox.options.reuse_existing_virtualenvs = True # TODO: Check if necessary


@nox.session(python=PYTHON_VERSIONS, tags=["citests"])
def tests(session):
    """Run the test suite."""
    session.install("pytest", "pytest-asyncio", "pytest-docker", "pytest-cov")
    session.install(".")
    session.run("pytest", "--cov", "--cov-report=term-missing")


@nox.session(python=DEFAULT_PYTHON)
def protos(session):
    session.install("grpcio-tools==1.62.3")
    session.run("./compile_protos.py", external=True)


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Lint the codebase using flake8."""
    session.install("flake8")
    session.run("flake8", "src/dataclay", "tests")


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Automatically format code with black and isort."""
    session.install("black", "isort")
    # Run isort before black
    session.run("isort", "--gitignore", ".")
    session.run("black", ".")


@nox.session(python=DEFAULT_PYTHON)
def mypy(session):
    """Run type checks using mypy."""
    session.install(".")
    session.install("mypy")
    session.run("mypy", "src/dataclay")


@nox.session(python=DEFAULT_PYTHON)
def safety(session):
    """Check for security vulnerabilities."""
    session.install(".")
    session.install("safety")
    session.run("safety", "check")


@nox.session()
def dev(session: nox.Session) -> None:
    """
    Set up a python development environment for the project at ".venv".
    """
    session.install("virtualenv")
    session.run("virtualenv", ".venv", silent=True)
    session.run(".venv/bin/pip", "install", "-e", ".[telemetry,dev]", external=True)


# TODO: Check https://nox.thea.codes/en/stable/cookbook.html#the-auto-release
