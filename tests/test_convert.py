from dataclasses import dataclass
from typing import Optional

import pytest

from configparser_override import ConfigParserOverride
from configparser_override.convert import ConfigConverter


@pytest.fixture()
def config_file_simple_types(tmp_path):
    config_content = """
    [DEFAULT]
    allkey = string

    [section1]
    key1 = 123
    key2 = string

    [section2]
    key3 = 1.2
    """
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


@dataclass
class DefaultSection:
    allkey: str


@dataclass
class Section1:
    key1: int
    key2: str
    allkey: str


@dataclass
class Section2:
    key3: float
    allkey: str


@dataclass
class ConfigFileSimpleTypes:
    DEFAULT: DefaultSection
    section1: Section1
    section2: Section2


@pytest.fixture()
def config_file_complex_types(tmp_path):
    config_content = """
    [DEFAULT]
    allkey = byte
    optionalallkey = 123

    [section1]
    key1 = [1,2,3,4,5,6]
    key2 = {"key": "value", "key2": "value2"}

    [section2]
    key3 = [1.2,1.4]
    """
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


@dataclass
class ComplexDefaultSection:
    allkey: bytes
    optionalallkey: Optional[str | int]


@dataclass
class ComplexSection1:
    # key1: list[list[int | str]]
    # key2: dict[str, dict[str, str]]
    key1: list[int | str]
    key2: dict[str, str]
    allkey: bytes
    optionalallkey: Optional[str | int]


@dataclass
class ComplexSection2:
    key3: list[float]
    allkey: bytes
    optionalallkey: Optional[str | int]
    key4: Optional[float] = None


@dataclass
class ConfigFileComlexTypes:
    DEFAULT: ComplexDefaultSection
    section1: ComplexSection1
    section2: ComplexSection2


@pytest.fixture()
def config_file_complex_types_nested(tmp_path):
    config_content = """
    [DEFAULT]
    allkey = byte
    optionalallkey = 123

    [section1]
    key1 = [[1,2,3],[4,5,6]]
    key2 = {"key": {"nestedkey": "value"}, "key2": {"nestedkey2": "value2"}}

    [section2]
    key3 = ["true",1,"yes"]

    [section3]
    key4 = {"string1","string2"}
    key5 = [{"string1"},{"string2"}]
    key6 = ({"123j"},{"4+2j"})
    """
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


@dataclass
class ComplexNestedDefaultSection:
    allkey: bytes
    optionalallkey: Optional[str | int]


@dataclass
class ComplexNestedSection1:
    key1: list[list[int | str]]
    key2: dict[str, dict[str, str]]
    allkey: bytes
    optionalallkey: Optional[str | int]


@dataclass
class ComplexNestedSection2:
    key3: list[Optional[bool | str]]
    allkey: bytes
    optionalallkey: Optional[str | int]
    key4: Optional[float] = None


@dataclass
class ComplexNestedSection3:
    key4: set[str]
    key5: list[set[str]]
    key6: tuple[set[complex]]


@dataclass
class ConfigFileComlexNestedTypes:
    DEFAULT: ComplexNestedDefaultSection
    section1: ComplexNestedSection1
    section2: ComplexNestedSection2
    section3: ComplexNestedSection3


def test_simple_config_to_dataclass(config_file_simple_types):
    parser = ConfigParserOverride()
    parser.read(filenames=config_file_simple_types)

    dataclass_rep = ConfigConverter(parser.config).config_to_dataclass(
        ConfigFileSimpleTypes
    )
    # dataclass_rep = config_to_dataclass(parser.config, ConfigFileSimpleTypes)
    assert dataclass_rep.DEFAULT.allkey == "string"
    assert dataclass_rep.section1.allkey == "string"
    assert dataclass_rep.section1.key1 == 123
    assert dataclass_rep.section1.key2 == "string"
    assert dataclass_rep.section2.key3 == 1.2


def test_complex_config_to_dataclass(config_file_complex_types):
    parser = ConfigParserOverride()
    parser.read(filenames=config_file_complex_types)

    dataclass_rep = ConfigConverter(parser.config).config_to_dataclass(
        ConfigFileComlexTypes
    )
    # dataclass_rep = config_to_dataclass(parser.config, ConfigFileComlexTypes)
    assert dataclass_rep.DEFAULT.allkey == b"byte"
    assert dataclass_rep.section1.allkey == b"byte"
    assert dataclass_rep.section1.key1 == [1, 2, 3, 4, 5, 6]
    assert dataclass_rep.section1.key2 == {
        "key": "value",
        "key2": "value2",
    }
    assert dataclass_rep.section2.key3 == [1.2, 1.4]


def test_complex_nested_config_to_dataclass(config_file_complex_types_nested):
    parser = ConfigParserOverride()
    parser.read(filenames=config_file_complex_types_nested)

    dataclass_rep = ConfigConverter(parser.config).config_to_dataclass(
        ConfigFileComlexNestedTypes
    )
    # dataclass_rep = config_to_dataclass(parser.config, ConfigFileComlexNestedTypes)
    assert dataclass_rep.DEFAULT.allkey == b"byte"
    assert dataclass_rep.section1.allkey == b"byte"
    assert dataclass_rep.section1.key1 == [[1, 2, 3], [4, 5, 6]]
    assert dataclass_rep.section1.key2 == {
        "key": {"nestedkey": "value"},
        "key2": {"nestedkey2": "value2"},
    }
    assert dataclass_rep.section2.key3 == [True, True, True]
    assert dataclass_rep.section3.key4 == {"string1", "string2"}
    assert dataclass_rep.section3.key5 == [{"string1"}, {"string2"}]
    assert dataclass_rep.section3.key6 == ({123j}, {4 + 2j})
