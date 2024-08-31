import configparser
from dataclasses import dataclass
from typing import Any, Callable, Optional

import pytest

from configparser_override import ConfigParserOverride
from configparser_override.convert import ConfigConverter
from configparser_override.exceptions import ConversionError, LiteralEvalMiscast


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
    key3 = ["true",1,"yes","no",0,"false"]

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
    assert dataclass_rep.DEFAULT.allkey == b"byte"
    assert dataclass_rep.section1.allkey == b"byte"
    assert dataclass_rep.section1.key1 == [[1, 2, 3], [4, 5, 6]]
    assert dataclass_rep.section1.key2 == {
        "key": {"nestedkey": "value"},
        "key2": {"nestedkey2": "value2"},
    }
    assert dataclass_rep.section2.key3 == [True, True, True, False, False, False]
    assert dataclass_rep.section3.key4 == {"string1", "string2"}
    assert dataclass_rep.section3.key5 == [{"string1"}, {"string2"}]
    assert dataclass_rep.section3.key6 == ({123j}, {4 + 2j})


def test_config_to_dataclass_custom_bools():
    custom_booleans = {"cool": True, "not cool": False}

    @dataclass
    class Sect1:
        true: bool
        false: bool

    @dataclass
    class CustomBools:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__true="cool", sect1__false="not cool")
    parser.read(filenames=[])

    dataclass_rep = ConfigConverter(
        parser.config, boolean_states=custom_booleans
    ).config_to_dataclass(CustomBools)

    assert dataclass_rep.sect1.false is False
    assert dataclass_rep.sect1.true is True


def test_config_to_dataclass_bools_not_valid():
    @dataclass
    class Sect1:
        true: bool
        false: bool

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(
        sect1__true="notValidTrue", sect1__false="notValidFalse"
    )
    parser.read(filenames=[])

    with pytest.raises(ValueError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_missing_key_in_config():
    @dataclass
    class Sect1:
        key: str
        key132: str

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key="ok")
    parser.read(filenames=[])

    with pytest.raises(AttributeError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_unsupported_type():
    @dataclass
    class Sect1:
        key: Callable

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key="ok")
    parser.read(filenames=[])

    with pytest.raises(ValueError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_list_member_conversion_error():
    @dataclass
    class Sect1:
        key: list[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_set_member_conversion_error():
    @dataclass
    class Sect1:
        key: set[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok"}')
    parser.read(filenames=[])

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_dict_member_conversion_error():
    @dataclass
    class Sect1:
        key: dict[str, int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok":"ok"}')
    parser.read(filenames=[])

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_tuple_member_conversion_error():
    @dataclass
    class Sect1:
        key: tuple[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='("ok","ok")')
    parser.read(filenames=[])

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_union_conversion_error():
    @dataclass
    class Sect1:
        key: list[int | float]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok","ok"]')
    parser.read(filenames=[])

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_list_member_literaleval_error():
    @dataclass
    class Sect1:
        key: list[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok"}')
    parser.read(filenames=[])

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_set_member_literaleval_error():
    @dataclass
    class Sect1:
        key: set[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_dict_member_literaleval_error():
    @dataclass
    class Sect1:
        key: dict[str, int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).config_to_dataclass(C)


def test_tuple_member_literaleval_error():
    @dataclass
    class Sect1:
        key: tuple[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).config_to_dataclass(C)


@pytest.fixture()
def config_file_allow_empty(tmp_path):
    config_content = """
    [sectionv]
    key1 = 123

    [sectione]
    key3
    """
    config_path = tmp_path / "config_allow_empty.ini"
    config_path.write_text(config_content)
    return str(config_path)


def test_none_type(config_file_allow_empty):
    @dataclass
    class SectionV:
        key1: int

    @dataclass
    class SectionE:
        key3: None

    @dataclass
    class ConfigEmptyKey:
        sectionv: SectionV
        sectione: SectionE

    parser = ConfigParserOverride(
        config_parser=configparser.ConfigParser(allow_no_value=True)
    )
    parser.read(filenames=[config_file_allow_empty])

    dataclass_rep = parser.to_dataclass(ConfigEmptyKey)
    assert dataclass_rep.sectione.key3 is None
    assert dataclass_rep.sectionv.key1 == 123


@pytest.fixture()
def config_file_any(tmp_path):
    config_content = """
    [section]
    key1 = 123
    """
    config_path = tmp_path / "config_any.ini"
    config_path.write_text(config_content)
    return str(config_path)


def test_any_type(config_file_any):
    @dataclass
    class Section:
        key1: Any

    @dataclass
    class ConfigAny:
        section: Section

    parser = ConfigParserOverride(config_parser=configparser.ConfigParser())
    parser.read(filenames=[config_file_any])

    dataclass_rep = parser.to_dataclass(ConfigAny)
    assert dataclass_rep.section.key1 == "123"
