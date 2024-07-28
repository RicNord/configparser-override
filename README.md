# ConfigParser Override

This library provides a utility class `ConfigParserOverride` that extends the
functionality of `configparser.ConfigParser` to allow overriding configuration
values with environment variables and directly assigned key-value arguments.

> **NOTE:** This library only depends on the Python standard library!

## Features

- Read configuration from one or more files.
- Override configuration values with environment variables.
- Override configuration values with directly assigned arguments.
- Support for optional environment variable prefix.

## Install

```sh
pip install configparser-override
```

## Usage

Example of how to use `ConfigParserOverride`:

### Example `config.ini` File

```ini
[DEFAULT]
default_key1 = default_value1
default_key2 = default_value2

[section1]
key1 = value1
key2 = value2

[section2]
key3 = value3
key4 = value4
```

### Python Code

```python
import os
from configparser_override import ConfigParserOverride

# Optionally set environment variables for overriding
os.environ['MYAPP_KEY1'] = 'overridden_default_value1'
os.environ['MYAPP__SECTION1_KEY1'] = 'overridden_value1'
os.environ['MYAPP__SECTION2_KEY3'] = 'overridden_value3'

# Initialize the parser with an optional environment variable prefix
parser = ConfigParserOverride(env_prefix='MYAPP', section2__key4="direct_override_value4")

# Read configuration from a file
config = parser.read(filenames='config.ini')

# Access the configuration
print(config.defaults()['default_key1'])  # Output: overridden_default_value1
print(config.defaults()['default_key2'])  # Output: default_value2
print(config['section1']['key1'])  # Output: overridden_value1
print(config['section1']['key2'])  # Output: value2
print(config['section2']['key3'])  # Output: overridden_value3
print(config['section2']['key4'])  # Output: direct_override_value4
```

### Note

Configuration values can be overridden in three ways, in order of precedence:

1. **Directly passed arguments** during initialization of the class.
2. **Environment variables**.
3. **Configuration files**.

The format for environment variable names is as follows:

- When **no prefix** is set: The format is `[KEY]`.
- When **a prefix** is set: The format is `[PREFIX]_[KEY]`.
- Sections are denoted with double underscores (`__`).
  - The format is `[PREFIX]__[SECTION]_[KEY]` or `[SECTION]_[KEY]` if no prefix
    is set.

For example, to override `key1` in `section1` with a prefix `MYAPP`, the
environment variable would be `MYAPP__SECTION1_KEY1`.

## Development

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

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
will build and publish the new version to PyPi.

### Documentation

[Sphinx](https://www.sphinx-doc.org/) is used to create documentation for the
project. To generate:

```shell
cd docs
make apidocs # Generates API reference documentation for the code of the project
make html # Generates HTML that can be viwed in the browser
```
