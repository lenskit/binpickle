import io
import zlib
import functools as ft

from hypothesis import given
import hypothesis.strategies as st

from binpickle.write import _align_pos, CKOut
from binpickle.codecs.blosc import _split_blocks


@given(st.integers(100, 10000000))
def test_align(n):
    res = _align_pos(n, 1024)
    assert res >= n
    assert res % 1024 == 0


@given(st.binary())
def test_checksum_bytes(data):
    out = io.BytesIO()
    cko = CKOut(out)
    cko.write(data)
    assert out.getbuffer() == data
    assert cko.bytes == len(data)
    assert cko.checksum == zlib.adler32(data)


@given(st.lists(st.binary(), min_size=1, max_size=10))
def test_checksum_multi_bytes(arrays):
    out = io.BytesIO()
    cko = CKOut(out)
    for a in arrays:
        cko.write(a)
    cat = ft.reduce(lambda b1, b2: b1 + b2, arrays)
    assert out.getbuffer() == cat
    assert cko.bytes == len(cat)
    assert cko.checksum == zlib.adler32(cat)


def test_split_empty_block():
    blocks = _split_blocks(memoryview(b''), 10)
    assert len(blocks) == 1
    assert blocks[0] == b''


def test_split_one_block():
    blocks = _split_blocks(memoryview(b'asdf'), 10)
    assert len(blocks) == 1
    assert blocks[0] == b'asdf'


def test_split_two_blocks():
    blocks = _split_blocks(memoryview(b'asdf'), 2)
    assert len(blocks) == 2
    assert blocks[0] == b'as'
    assert blocks[1] == b'df'


def test_split_blocks_mismatch():
    blocks = _split_blocks(memoryview(b'asdfg'), 2)
    assert len(blocks) == 3
    assert blocks[0] == b'as'
    assert blocks[1] == b'df'
    assert blocks[2] == b'g'
