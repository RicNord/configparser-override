# ConfigParser Override

[![Version](https://img.shields.io/pypi/v/configparser-override?color=blue)](https://pypi.org/project/configparser-override/)
[![Build Status](https://github.com/RicNord/configparser-override/actions/workflows/ci.yaml/badge.svg)](https://github.com/RicNord/configparser-override/actions)

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

[SECTION1]
key1 = value1
key2 = value2

[SECTION2]
key3 = value3
key4 = value4
```

### Python Code

```python
import os
from configparser_override import ConfigParserOverride

# Optionally set environment variables for overriding
os.environ['MYAPP_DEFAULT_KEY1'] = 'overridden_default_value1'
os.environ['MYAPP_SECTION1__KEY1'] = 'overridden_value1'
os.environ['MYAPP_SECTION2__KEY3'] = 'overridden_value3'

# Initialize the parser with an optional environment variable prefix
parser = ConfigParserOverride(env_prefix='MYAPP_', SECTION2__KEY4="direct_override_value4")

# Read configuration from a file
config = parser.read(filenames='config.ini')

# Access the configuration
print(config.defaults()['default_key1'])  # Output: overridden_default_value1
print(config.defaults()['default_key2'])  # Output: default_value2
print(config['SECTION1']['key1'])  # Output: overridden_value1
print(config['SECTION1']['key2'])  # Output: value2
print(config['SECTION2']['key3'])  # Output: overridden_value3
print(config['SECTION2']['key4'])  # Output: direct_override_value4
```

### Note

Configuration values can be overridden in three ways, in order of precedence:

1. **Directly passed arguments** during initialization of the class.
2. **Environment variables**.
3. **Configuration files**.

The format for environment variable names is as follows:

- When **no prefix** is set: The format is `[OPTION]`.
- When **a prefix** is set: The format is `[PREFIX][OPTION]`.
- Sections and options are denoted with double underscores (`__`).
  - The format is `[PREFIX][SECTION]__[OPTION]` or `[SECTION]__[OPTION]` if no prefix
    is set.

For example, to override the option `key1` in `SECTION1` with a prefix
`MYAPP_`, the environment variable would be `MYAPP_SECTION1__KEY1`.

#### Platform dependency

Different Operating systems handle environment variables differently. Linux is
case sensitive while Windows is not see [os.environ
docs](https://docs.python.org/3/library/os.html#os.environ). Hence it is safest
to always use capitalized environment variables and Section names to avoid any
unexpected behavior.
