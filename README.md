# ConfigParser Override

[![Version](https://img.shields.io/pypi/v/configparser-override?color=blue)](https://pypi.org/project/configparser-override/)
[![Build
Status](https://github.com/RicNord/configparser-override/actions/workflows/ci.yaml/badge.svg)](https://github.com/RicNord/configparser-override/actions)

`ConfigParserOverride` enhances the
[ConfigParser](https://docs.python.org/3/library/configparser.html) by allowing
you to override options from a configuration file or add new options using;
environment variables and directly assigned key-value arguments.

> **NOTE:** This package only depends on the Python Standard Library!

## Features

- Read configuration from one or more files.
- Override configuration options with environment variables.
- Override configuration options with directly assigned arguments.
- Optional environment variable prefix support.
- Convert configuration objects to a dataclass and cast the values to
  predefined datatypes.
- Find and collect configuration files in conventional locations

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
    # Sections & options are case insensitive by default
    SECTION2__KEY4="direct_override_value4",
    section2__key5="direct_override_value5",
)

# Read configuration from a file
parser.read(filenames="config.ini")
config = parser.config

# Access the configuration
print(config.defaults()["default_key1"])  # Output: overridden_default_value1
print(config.defaults()["default_key2"])  # Output: default_value2
print(config["section1"]["key1"])  # Output: overridden_value1
print(config["section1"]["key2"])  # Output: value2
print(config["section2"]["key3"])  # Output: overridden_value3
print(config["section2"]["key4"])  # Output: direct_override_value4
print(config["section2"]["key5"])  # Output: direct_override_value5
```

#### Configuration source precedence

Configuration options can be overridden in three ways. This is the order of
precedence:

1. **Directly assigned arguments** during initialization of the
   `ConfigParserOverride` class.
2. **Environment variables**.
3. **Configuration files**.

#### Environment variable configuration

To override configuration options, use environment variables with the following
format. Separate sections and options using double underscores (`__`):

- **With Prefix** (`MYAPP_` as an example):
  - For `DEFAULT` section: `[PREFIX][OPTION]`
  - For other sections: `[PREFIX][SECTION]__[OPTION]`

- **No Prefix**:
  - For `DEFAULT` section: `[OPTION]`
  - For other sections: `[SECTION]__[OPTION]`

**Example**:

- To override `key1` in `section1` with prefix `MYAPP_`, use
  `MYAPP_SECTION1__KEY1`.

## Find and collect configuration files

The library also contains a helper function `config_file_collector` that will
search for configuration files in conventional locations based on your OS.
The collected files can then be used as input to `ConfigParserOverride.read()`

### Searched paths

#### Linux and MacOS

Unix systems follows [XDG base directory
specification](https://specifications.freedesktop.org/basedir-spec/latest/) and
used environment variables:

- **XDG_CONFIG_HOME** (User config)
  - Default to **$HOME/.config**
- **XDG_CONFIG_DIRS** (System wide config)
  - List of directories separated by semicolon `:`
  - Default to **/etc/xdg**

#### Windows

Windows paths are specific in environment variables:

- **APPDATA** (User config)
  - Usually: **C:\Users\USERNAME\AppData\Roaming**
- **PROGRAMDATA** (System wide config)
  - Usually: **C:\ProgramData**

### Example

```python
from configparser_override import ConfigParserOverride, config_file_collector

collected_files = config_file_collector(file_name="config.ini", app_name="myapp")

print(collected_files)
# For Linux and MacOS
# Output: ["/etc/xdg/myapp/config.ini", "/home/USERNAME/.config/myapp/config.ini"]

# For Windows
# Output: ["C:/ProgramData/myapp/config.ini", "C:/Users/USERNAME/AppData/Roaming/myapp/config.ini"]

parser = ConfigParserOverride()
parser.read(filenames=collected_files)
config = parser.config
```

## Convert to a Dataclass and Validate Data Types

The library features a `ConfigConverter` class, which enables the conversion of
configuration data into a dataclass instance. This functionality is
particularly useful for ensuring that the configuration adheres to the expected
format, since it tries to cast the option in the config to the types in the
dataclass. Hence, it also allows you to take advantage of various typing
frameworks and tools, such as integrations with your text editor, providing
enhanced validation and code assistance.

### Example

```python
from dataclasses import dataclass
from typing import Optional

from configparser_override import ConfigParserOverride


@dataclass
class Section1:
    key1: int
    key2: list[str]
    key3: Optional[str] = None


@dataclass
class ExampleConfig:
    section1: Section1


# Initialize the parser with overrides
parser = ConfigParserOverride(
    section1__key1="42", section1__key2="['item1', 'item2']"
)

# Read configuration from **optional** file
parser.read(filenames=[])

# Convert to dataclass
config_as_dataclass = parser.to_dataclass(ExampleConfig)
print(config_as_dataclass.section1.key1)  # Output: 42
print(type(config_as_dataclass.section1.key1))  # Output: <class 'int'>
print(config_as_dataclass.section1.key2)  # Output: ['item1', 'item2']
print(type(config_as_dataclass.section1.key2))  # Output: <class 'list'>
print(config_as_dataclass.section1.key3)  # Output: None
```

### Data Types

Supported data types are:

- String
- Integer
- Bool
- Float
- Complex
- Bytes

Collections (nesting is supported):

- List
- Dict
- Set
- Tuple

Others:

- None
- Optional | Option does not need to exist in config
- Union | Tries to cast until successful, in the order the types are specified
- Any | no type cast

## Platform Dependency

Different operating systems handle environment variables differently. Linux is
case sensitive while Windows is not. See [os.environ
docs](https://docs.python.org/3/library/os.html#os.environ). Hence, it is safest
to always use capitalized environment variables to avoid any unexpected
behavior.

### Recommendation

In order to avoid any unanticipated issues and make your code safe to run on
any platform, follow these rules:

| Element                       | Recommended Case |
|-------------------------------|------------------|
| Environment variables         | UPPERCASE        |
| Environment variable prefix   | UPPERCASE        |
| DEFAULT section in config.ini (as per convention in the standard library ConfigParser) | UPPERCASE |
| Sections in config.ini files  | lowercase        |
| Options in config.ini files   | lowercase        |
| Directly assigned arguments   | lowercase        |

### Case Sensitivity Handling

By default, `ConfigParserOverride` tries to stores everything as lowercase,
with the exception of `Section` headers that are read from configuration files,
where the existing casing in the file is honored. However, if you want to
override such a section with an environment variable or direct assignment, it
will recognize the existing casing of the section and continue to use that even
though you use other casing in the override method.

It is highly discouraged, but you can make `ConfigParserOverride` case-sensitive
by initializing it with the argument `case_sensitive_overrides=True`.

```python
from configparser_override import ConfigParserOverride

parser = ConfigParserOverride(env_prefix="MYAPP_", case_sensitive_overrides=True)
```
