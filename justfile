set dotenv-load

# Just is a command runner. It can be used to provide a shorthand to run
# complex commands, for example `just lint` for `python -m kensho_lint.lint...`

# Here are some installation instructions:
# https://github.com/casey/just?tab=readme-ov-file#installation
# Once installed, you can run any of the commands in this file by
# prepending them with `just`, for example `just lint` to run the linter.
# Run `just` shows a list of all available commands

# If there are commands that you believe can be useful to other contributors,
# feel free to add them.


default:
    just --list

alias l := lint
# Lint the app directory (both lint and l work). For verbose, use `just lint --verbose`
lint *args:
    python -m mypy --config-file pyproject.toml kfinance {{args}}
    # The ruff linters (check) and formatters (format) are separate.
    # See https://docs.astral.sh/ruff/formatter/#sorting-imports
    python -m ruff --config pyproject.toml check kfinance --fix {{args}}
    python -m ruff --config pyproject.toml format kfinance {{args}}
    nbqa mypy example_notebooks

alias t := unit-test
# Run unit tests. Use args for optional settings
unit-test *args:
    python -m pytest {{args}}

# Build the sphinx documents locally
# First, copy the dependencies in docs/requirements.txt into pyproject.toml and install in a venv.
# Don't merge changes to pyproject and docs/output into the remote repo!
sphinx *args:
    PYTHONPATH="${PYTHONPATH:-}:." sphinx-build docs docs/output

# Install all dependencies including dev dependencies
install-deps:
    pip install -e .[dev]
