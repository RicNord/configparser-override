from configparser_override.types import SecretBytes, SecretStr


def test_secret_str_base():
    s = SecretStr("test")

    assert str(s) == "**********"
    assert s.__hash__() == hash("test")
    assert s.get_secret_value() == "test"
    assert repr(s) == 'SecretStr(value="**********")'
    assert len(s) == 4


def test_secret_str_comp():
    s = SecretStr("test")
    o = SecretStr("test")
    d = SecretStr("test2")

    assert s == o
    assert s != d


def test_empty_str():
    s = SecretStr("")

    assert len(s) == 0
    assert str(s) == ""


def test_secret_bytes_base():
    s = SecretBytes(b"test")

    assert str(s) == "**********"
    assert s.__hash__() == hash(b"test")
    assert s.get_secret_value() == b"test"
    assert repr(s) == 'SecretBytes(value=b"**********")'
    assert len(s) == 4


def test_secret_bytes_comp():
    s = SecretBytes(b"test")
    o = SecretBytes(b"test")
    d = SecretBytes(b"test2")

    assert s == o
    assert s != d


def test_empty_bytes():
    s = SecretBytes("")

    assert len(s) == 0
    assert str(s) == ""
