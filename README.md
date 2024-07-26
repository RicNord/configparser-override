# ConfigEnvParser

Configparser with enviorment variable override

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## Install

- TODO | How to install this project

## Usage

- TODO | How to use this project



## Development

To list available commands for your convenience:

```shell
make help
```

### Local environment setup

```shell
python3 -m venv ./venv
source ./venv/bin/activate # Linux and MacOS
venv\Scripts\activate # Windows

pip install --editable .[dev]
```

### Run tests

```shell
make pytest # Run pytest
make style # Run lint formatting and type check
make test-all # Run all tests with tox

make auto-fix # Auto-fix possible style issues
```

### Pre-commit hooks

To install optional [pre-commit](https://pre-commit.com/) hooks; after
environment set-up run:

```bash
pre-commit install
```

## Project maintenance

Intended for project maintainers

### Release

[Bump my version](https://callowayproject.github.io/bump-my-version/) is used
to bump the semantic version of the project.

For details see:

```shell
bump-my-version bump --help
```

Bump my version is configured to create a `new commit` and `tag` it with the
new version when a version is bumped.
When a new tag is pushed to github the
[publish-pypi workflow](./.github/workflows/publish-pypi.yaml) is triggered and
will build and publish the new version to PyPi. You will need to configure
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for this to
work. There is also an option to trigger the workflow manually and publish to
the [test](https://test.pypi.org/) instance of PyPi.

To manually publish to [PyPi](https://pypi.org/) run:

```shell
make publish-test # Publish pkg to PyPi test instance
make publish # Publish pkg to PyPi
```

This will build the project and publish to PyPi with help of
[Twine](https://twine.readthedocs.io/en/stable/). For authentication and
additional target repositories refer to your
[.pypirc](https://packaging.python.org/en/latest/specifications/pypirc/)
configuration file.

### Documentation

[Sphinx](https://www.sphinx-doc.org/) is used to create documentation for the
project. To generate:

```shell
cd docs
make apidocs # Generates API reference documentation for the code of the project
make html # Generates HTML that can be viwed in the browser
```

This documentation can be hosted on eg. [Read The
Docs](https://about.readthedocs.com/) for easy accessibility.
