from pytest import raises

from binpickle.format import *


def test_format_sizes():
    assert HEADER_FORMAT.size == 16
    assert TRAILER_FORMAT.size == 16


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
    with raises(ValueError) as exc:
        FileHeader.decode(b'BNPQ\x00\x00\x00\x00' + (b'\x00' * 8))
    assert 'magic' in str(exc.value)


def test_catch_bad_version():
    with raises(ValueError) as exc:
        FileHeader.decode(b'BPCK\x00\x08\x00\x00' + (b'\x00' * 8))
    assert 'version' in str(exc.value)


def test_catch_bad_padding():
    with raises(ValueError) as exc:
        FileHeader.decode(b'BPCK\x00\x01\x00\xff' + (b'\x00' * 8))
    assert 'padding' in str(exc.value)


def test_index_empty():
    index = FileIndex()
    assert len(index) == 0
    assert len(index.buffers) == 0
    i2 = FileIndex.unpack(index.pack())
    assert len(i2) == 0


def test_index_empty_v1():
    index = FileIndex(version=1)
    assert len(index) == 0
    assert len(index.buffers) == 0
    ipack = index.pack()
    assert len(ipack) == 1
    i2 = FileIndex.unpack(ipack)
    assert len(i2) == 0
