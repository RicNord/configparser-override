# ConfigParser Override

[![Version](https://img.shields.io/pypi/v/configparser-override?color=blue)](https://pypi.org/project/configparser-override/)
[![Build Status](https://github.com/RicNord/configparser-override/actions/workflows/ci.yaml/badge.svg)](https://github.com/RicNord/configparser-override/actions)

This library provides a utility class `ConfigParserOverride` that extends the
functionality of
[`configparser.ConfigParser`](https://docs.python.org/3/library/configparser.html)
to allow overriding configuration values with environment variables and
directly assigned key-value arguments.

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
os.environ["MYAPP_DEFAULT_KEY1"] = "overridden_default_value1"
os.environ["MYAPP_SECTION1__KEY1"] = "overridden_value1"
os.environ["MYAPP_SECTION2__KEY3"] = "overridden_value3"

# Initialize the parser with an optional environment variable prefix and
# overrides from direct assignments.
parser = ConfigParserOverride(
    env_prefix="MYAPP_",
    SECTION2__KEY4="direct_override_value4",
    section2__key5="direct_override_value5",  # By default sections and keys are case insensitive
)

# Read configuration from a file
config = parser.read(filenames="config.ini")

# Access the configuration
print(config.defaults()["default_key1"])  # Output: overridden_default_value1
print(config.defaults()["default_key2"])  # Output: default_value2
print(config["section1"]["key1"])  # Output: overridden_value1
print(config["section1"]["key2"])  # Output: value2
print(config["section2"]["key3"])  # Output: overridden_value3
print(config["section2"]["key4"])  # Output: direct_override_value4
print(config["section2"]["key5"])  # Output: direct_override_value5
```

### Note

Configuration values can be overridden in three ways. This is the order of
precedence:

1. **Directly assigned arguments** during initialization of the class.
2. **Environment variables**.
3. **Configuration files**.

The format for environment variable names is as follows:

- When **no prefix** is set: The format is `[OPTION]`.
- When **a prefix** is set: The format is `[PREFIX][OPTION]`.
- Sections and options are separated by double underscores (`__`).
  - The format is `[PREFIX][SECTION]__[OPTION]` or `[SECTION]__[OPTION]` if no prefix
    is set.

For example, to override the option `key1` in `section1` with a prefix
`MYAPP_`, the environment variable would be `MYAPP_SECTION1__KEY1`.

## Platform Dependency

Different operating systems handle environment variables differently. Linux is
case sensitive while Windows is not. See [os.environ
docs](https://docs.python.org/3/library/os.html#os.environ). Hence, it is safest
to always use capitalized environment variables to avoid any unexpected
behavior.

### Recommendation

In order to avoid any unanticipated issues and make your code safe to run on
any platform, follow these rules:

- `Environment variables` should be `UPPERCASE`.
  - `Environment variable prefix` should be `UPPERCASE`.
- `Sections` in config.ini files should be `lowercase`.
  - One exception is the `DEFAULT` section which by convention is `UPPERCASE`.
- `Options` in config.ini files should be `lowercase`.
- `Directly assigned arguments` should be `lowercase`.

### Default Case Sensitivity Handling

By default, `ConfigParserOverride` stores everything as lowercase, with an
exception of `Section` headers that are read from configuration files, where
the existing casing is honored. However, if you want to override something
with an environment variable or direct assignment, it will recognize the
existing casing of the section and continue to use that even though you use
uppercase or something else in the override.

It is highly discouraged, but you can make `ConfigParserOverride` case-sensitive
by initializing it with the argument `case_sensitive_overrides=True`.

```python
from configparser_override import ConfigParserOverride

parser = ConfigParserOverride(env_prefix="MYAPP_", case_sensitive_overrides=True)
```
