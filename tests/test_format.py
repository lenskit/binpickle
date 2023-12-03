from pytest import raises

from binpickle.errors import FormatError
from binpickle.format import FileHeader, FileTrailer, HEADER_FORMAT, TRAILER_FORMAT


def test_format_sizes():
    assert HEADER_FORMAT.size == 16
    assert FileHeader.SIZE == 16
    assert TRAILER_FORMAT.size == 44
    assert FileTrailer.SIZE == 44


def test_pack_default_header():
    h = FileHeader()
    bs = h.encode()
    assert len(bs) == 16


def test_default_header_round_trip():
    h = FileHeader()
    bs = h.encode()
    assert len(bs) == 16

    h2 = FileHeader.decode(bs)
    assert h2 is not h
    assert h2 == h


def test_size_round_trip():
    h = FileHeader(length=57)
    bs = h.encode()
    assert len(bs) == 16

    h2 = FileHeader.decode(bs)
    assert h2.length == 57
    assert h2 == h


def test_catch_bad_magic():
    with raises(FormatError) as exc:
        FileHeader.decode(b"BNPQ\x00\x00\x00\x00" + (b"\x00" * 8))
    assert "magic" in str(exc.value)


def test_catch_bad_version():
    with raises(FormatError) as exc:
        FileHeader.decode(b"BPCK\x00\x12\x00\x00" + (b"\x00" * 8))
    assert "invalid version" in str(exc.value)


def test_catch_bad_padding():
    with raises(FormatError) as exc:
        FileHeader.decode(b"BPCK\x00\x02\x00\xff" + (b"\x00" * 8))
    assert "unsupported flags" in str(exc.value)
