import configparser
import platform
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, Optional, get_type_hints

import pytest

from configparser_override import ConfigParserOverride
from configparser_override.convert import (
    ConfigConverter,
    _can_ignore_conversion,
    _can_ignore_section,
    _field_has_default_value,
    _is_optional_dataclass,
    _is_optional_type,
)
from configparser_override.exceptions import (
    ConversionError,
    ConversionIgnoreError,
    InvalidParametersError,
    LiteralEvalMiscast,
)
from configparser_override.types import SecretBytes, SecretStr


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
    parser.apply_overrides()

    dataclass_rep = ConfigConverter(parser.config).to_dataclass(ConfigFileSimpleTypes)
    assert dataclass_rep.DEFAULT.allkey == "string"
    assert dataclass_rep.section1.allkey == "string"
    assert dataclass_rep.section1.key1 == 123
    assert dataclass_rep.section1.key2 == "string"
    assert dataclass_rep.section2.key3 == 1.2


def test_complex_config_to_dataclass(config_file_complex_types):
    parser = ConfigParserOverride()
    parser.read(filenames=config_file_complex_types)
    parser.apply_overrides()

    dataclass_rep = ConfigConverter(parser.config).to_dataclass(ConfigFileComlexTypes)
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
    parser.apply_overrides()

    dataclass_rep = ConfigConverter(parser.config).to_dataclass(
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
    parser.apply_overrides()

    dataclass_rep = ConfigConverter(
        parser.config, boolean_states=custom_booleans
    ).to_dataclass(CustomBools)

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
    parser.apply_overrides()

    with pytest.raises(ValueError):
        ConfigConverter(parser.config).to_dataclass(C)


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
    parser.apply_overrides()

    with pytest.raises(ConversionIgnoreError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_ignore_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key132: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    parser = ConfigParserOverride(sect1__key="ok", sect2__key="ignore_me")
    parser.read(filenames=[])
    parser.apply_overrides()

    dc_config = ConfigConverter(parser.config).to_dataclass(C)
    assert parser.config["sect2"]["key"] == "ignore_me"
    assert dc_config.sect1.key == "ok"
    assert dc_config.sect2 is None


def test_dont_ignore_default_none_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    config = configparser.ConfigParser()
    config.add_section("sect1")
    config.set(section="sect1", option="key", value="a")
    config.add_section("sect2")
    config.set(section="sect2", option="key", value="b")
    config.set(section="sect2", option="key123", value="c")

    dc_config = ConfigConverter(config).to_dataclass(C)
    assert config["sect1"]["key"] == "a"
    assert config["sect2"]["key"] == "b"
    assert dc_config.sect1.key == "a"
    assert dc_config.sect2 is not None
    assert dc_config.sect2.key == "b"
    assert dc_config.sect2.key123 == "c"


def test_optional_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    parser = ConfigParserOverride(
        sect1__key="ok", sect2__key="ok1", sect2__key123="ok123"
    )
    parser.read(filenames=[])
    parser.apply_overrides()

    dc_config = ConfigConverter(parser.config).to_dataclass(C)
    assert parser.config["sect2"]["key"] == "ok1"
    assert dc_config.sect1.key == "ok"
    assert dc_config.sect2 is not None
    assert dc_config.sect2.key == "ok1"


def test_exclude_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    parser = ConfigParserOverride(
        sect1__key="ok",
    )
    parser.read(filenames=[])
    parser.apply_overrides()

    dc_config = ConfigConverter(parser.config, exclude_sections=["sect2"]).to_dataclass(
        C
    )
    assert dc_config.sect1.key == "ok"
    assert dc_config.sect2 is None


def test_exclude_non_optional_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Sect2

    parser = ConfigParserOverride(
        sect1__key="ok",
    )
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionIgnoreError):
        ConfigConverter(parser.config, exclude_sections=["sect2"]).to_dataclass(C)


def test_dont_exclude_optional_full_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    config = configparser.ConfigParser()
    config.add_section("sect1")
    config.set(section="sect1", option="key", value="a")
    config.add_section("sect2")
    config.set(section="sect2", option="key", value="b")
    config.set(section="sect2", option="key123", value="c")

    dc_config = ConfigConverter(config).to_dataclass(C)
    assert dc_config.sect2 is not None
    assert dc_config.sect1.key == "a"
    assert dc_config.sect2.key == "b"
    assert dc_config.sect2.key123 == "c"


def test_know_to_use_default_value():
    @dataclass
    class Sect1:
        key: str = "a"

    @dataclass
    class Sect2:
        key: str
        key123: str = "c"

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    config = configparser.ConfigParser()
    config.add_section("sect2")
    config.set(section="sect2", option="key", value="b")

    dc_config = ConfigConverter(config).to_dataclass(C)
    assert dc_config.sect2 is not None
    assert dc_config.sect1.key == "a"
    assert dc_config.sect2.key == "b"
    assert dc_config.sect2.key123 == "c"


def test_all_optional_sections_none():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Optional[Sect1] = None
        sect2: Optional[Sect2] = None

    config = configparser.ConfigParser()

    dc_config = ConfigConverter(config).to_dataclass(C)
    assert dc_config.sect1 is None
    assert dc_config.sect2 is None


def test_exclude_optional_section_config():
    @dataclass
    class Sect1:
        key: str

    @dataclass
    class Sect2:
        key: str
        key123: str

    @dataclass
    class C:
        sect1: Sect1
        sect2: Optional[Sect2] = None

    parser = ConfigParserOverride(
        sect1__key="ok",
    )
    parser.read(filenames=[])
    parser.apply_overrides()

    dc_config = ConfigConverter(parser.config, exclude_sections=["sect2"]).to_dataclass(
        C
    )
    assert dc_config.sect2 is None
    assert dc_config.sect1.key == "ok"


def test_unsupported_type():
    @dataclass
    class Sect1:
        key: Callable

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key="ok")
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ValueError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_list_member_conversion_error():
    @dataclass
    class Sect1:
        key: list[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_set_member_conversion_error():
    @dataclass
    class Sect1:
        key: set[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok"}')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_dict_member_conversion_error():
    @dataclass
    class Sect1:
        key: dict[str, int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok":"ok"}')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_tuple_member_conversion_error():
    @dataclass
    class Sect1:
        key: tuple[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='("ok","ok")')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_union_conversion_error():
    @dataclass
    class Sect1:
        key: list[int | float]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok","ok"]')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(ConversionError):
        ConfigConverter(parser.config).to_dataclass(C)


def test_list_member_literaleval_error():
    @dataclass
    class Sect1:
        key: list[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='{"ok"}')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).to_dataclass(C)


def test_set_member_literaleval_error():
    @dataclass
    class Sect1:
        key: set[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).to_dataclass(C)


def test_dict_member_literaleval_error():
    @dataclass
    class Sect1:
        key: dict[str, int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).to_dataclass(C)


def test_tuple_member_literaleval_error():
    @dataclass
    class Sect1:
        key: tuple[int]

    @dataclass
    class C:
        sect1: Sect1

    parser = ConfigParserOverride(sect1__key='["ok"]')
    parser.read(filenames=[])
    parser.apply_overrides()

    with pytest.raises(LiteralEvalMiscast):
        ConfigConverter(parser.config).to_dataclass(C)


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
    parser.apply_overrides()

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
    parser.apply_overrides()

    dataclass_rep = parser.to_dataclass(ConfigAny)
    assert dataclass_rep.section.key1 == "123"


@pytest.fixture()
def config_file_path(tmp_path):
    config_content = """
    [section]
    key1 = relative/path
    key2 = /absolut/unix/path
    key3 = c:/absolut/windows/path
    """
    config_path = tmp_path / "config_any.ini"
    config_path.write_text(config_content)
    return str(config_path)


def test_path_type(config_file_path):
    @dataclass
    class Section:
        key1: Path
        key2: Path
        key3: Path

    @dataclass
    class ConfigAny:
        section: Section

    parser = ConfigParserOverride(config_parser=configparser.ConfigParser())
    parser.read(filenames=[config_file_path])
    parser.apply_overrides()

    dataclass_rep = parser.to_dataclass(ConfigAny)
    assert dataclass_rep.section.key1 == Path("relative/path")
    assert dataclass_rep.section.key2 == Path("/absolut/unix/path")
    assert dataclass_rep.section.key3 == Path("c:/absolut/windows/path")
    assert dataclass_rep.section.key1.resolve().is_relative_to(Path.cwd())
    assert not dataclass_rep.section.key1.is_absolute()

    system = platform.system()

    if system == "Windows":
        assert not dataclass_rep.section.key2.is_absolute()
        assert dataclass_rep.section.key3.is_absolute()
    else:  # UNIX
        assert dataclass_rep.section.key2.is_absolute()
        assert not dataclass_rep.section.key3.is_absolute()


def test_is_optional_type_true():
    assert _is_optional_type(Optional[int])
    assert _is_optional_type(Optional[str])


def test_is_optional_type_false():
    assert not _is_optional_type(int)
    assert not _is_optional_type(str)


def test_is_optional_dataclass_true():
    @dataclass
    class C:
        a: int

    @dataclass
    class C2:
        a: int
        b: C
        c: Optional[C] = None

    t = get_type_hints(C2)
    assert _is_optional_dataclass(Optional[C])
    assert _is_optional_dataclass(t["c"])
    assert not _is_optional_dataclass(t["b"])


def test_is_optional_dataclass_false():
    @dataclass
    class C:
        a: int

    assert not _is_optional_dataclass(C)
    assert not _is_optional_dataclass(C(a=1))
    assert not _is_optional_dataclass(Optional[int])


def test_can_ignore_section():
    @dataclass
    class C:
        a: int

    @dataclass
    class C2:
        c: Optional[C] = None

    f = fields(C2)
    fc = fields(C)
    assert _can_ignore_section(f[0])
    assert not _can_ignore_section(fc[0])


def test_can_ignore_conversion():
    @dataclass
    class C:
        a: int

    @dataclass
    class C2:
        c: Optional[C] = None

    f = fields(C2)
    fc = fields(C)
    assert _can_ignore_conversion(f[0])
    assert not _can_ignore_conversion(fc[0])


def test_field_has_default_value():
    @dataclass
    class C1:
        a: int = 1

    @dataclass
    class C:
        a: int

    @dataclass
    class C2:
        c: Optional[C] = None

    f = fields(C)
    f1 = fields(C1)
    f2 = fields(C2)
    assert not _field_has_default_value(f[0])
    assert _field_has_default_value(f1[0])
    assert _field_has_default_value(f2[0])


def test_parse_section():
    config = configparser.ConfigParser()
    config.add_section("abc")
    config.set(section="abc", option="a", value="1")
    config.add_section("def")
    config.set(section="def", option="a", value="1")

    converter = ConfigConverter(config, include_sections=["abc"])
    assert converter._parse_section("abc")
    assert not converter._parse_section("def")


def test_too_many_args():
    config = configparser.ConfigParser()

    with pytest.raises(InvalidParametersError):
        ConfigConverter(config, include_sections=["abc"], exclude_sections=["def"])


def _factory_str() -> str:
    return "factory_str"


def _factory_int() -> int:
    return 1


def test_default_factory_in_dataclass():
    @dataclass
    class B:
        s: str = field(default_factory=_factory_str)

    @dataclass
    class A:
        i: Optional[int] = field(default_factory=_factory_int)

    @dataclass
    class C:
        b: B
        a: Optional[A] = None

    config = configparser.ConfigParser()

    converter = ConfigConverter(config).to_dataclass(C)

    assert converter.a is not None
    assert converter.a.i == 1
    assert converter.b is not None
    assert converter.b.s == "factory_str"


def test_default_factory_in_dataclass_is_override():
    @dataclass
    class B:
        s: str = field(default_factory=_factory_str)

    @dataclass
    class A:
        i: Optional[int] = field(default_factory=_factory_int)

    @dataclass
    class C:
        b: B
        a: Optional[A] = None

    config = configparser.ConfigParser()
    config.add_section("a")
    config.set(section="a", option="i", value="2")
    config.add_section("b")
    config.set(section="b", option="s", value="not_factory")

    converter = ConfigConverter(config).to_dataclass(C)

    assert converter.a is not None
    assert converter.a.i == 2
    assert converter.b is not None
    assert converter.b.s == "not_factory"


def test_secret_types(config_file_allow_empty):
    @dataclass
    class A:
        key1: SecretStr
        key2: Optional[SecretStr] = None

    @dataclass
    class B:
        key3: SecretBytes

    @dataclass
    class C:
        a: A
        b: B

    config = configparser.ConfigParser()
    config.add_section("a")
    config.set(section="a", option="key1", value="sensitive")
    config.add_section("b")
    config.set(section="b", option="key3", value="sensBytes")

    dataclass_rep = ConfigConverter(config).to_dataclass(C)
    assert dataclass_rep.a.key2 is None
    assert dataclass_rep.a.key1 == SecretStr(value="sensitive")
    assert len(dataclass_rep.a.key1) == len("sensitive")
    assert str(dataclass_rep.a.key1) == "**********"
    assert dataclass_rep.a.key1.get_secret_value() == "sensitive"

    assert dataclass_rep.b.key3 == SecretBytes(value=b"sensBytes")
    assert len(dataclass_rep.b.key3) == len(b"sensBytes")
    assert str(dataclass_rep.b.key3) == "**********"
    assert dataclass_rep.b.key3.get_secret_value() == b"sensBytes"
