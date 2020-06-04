import logging
import io
import zlib
import functools as ft

import numpy as np

from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
import pytest

from binpickle.write import _align_pos, CKOut

_log = logging.getLogger(__name__)


def _split_blocks(*args):
    blosc = pytest.importorskip('binpickle.codecs.blosc')
    return blosc._split_blocks(*args)


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
    assert blocks[0].nbytes == 2
    assert blocks[1].nbytes == 2


def test_split_blocks_mismatch():
    blocks = _split_blocks(memoryview(b'asdfg'), 2)
    assert len(blocks) == 3
    assert blocks[0] == b'as'
    assert blocks[0].nbytes == 2
    assert blocks[1] == b'df'
    assert blocks[1].nbytes == 2
    assert blocks[2] == b'g'
    assert blocks[2].nbytes == 1


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.data())
def test_split_blocks(data):
    bs = data.draw(st.integers(8, 4096))
    input = data.draw(st.binary(min_size=bs//2, max_size=bs*8))
    _log.info('input size %d, block size %d', len(input), bs)
    blocks = _split_blocks(memoryview(input), bs)
    _log.info('split into %d blocks', len(blocks))
    assert all(b.nbytes <= bs for b in blocks)
    assert all(len(b) <= bs for b in blocks)
    assert sum(b.nbytes for b in blocks) == len(input)
    reconst = ft.reduce(lambda buf, block: buf + block, blocks, bytes())
    assert len(reconst) == len(input)
    assert reconst == input


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.data())
def test_split_arrays(data):
    bs = data.draw(st.integers(8, 4096))
    size = data.draw(st.integers(bs//8, bs*4))
    array = np.random.randn(size)
    input = memoryview(array)
    _log.info('input size %d (%d bytes), block size %d', len(input), input.nbytes, bs)
    blocks = _split_blocks(memoryview(input), bs)
    _log.info('split into %d blocks', len(blocks))
    assert all(b.nbytes <= bs for b in blocks)
    assert all(len(b) <= bs for b in blocks)
    assert sum(b.nbytes for b in blocks) == input.nbytes
    reconst = ft.reduce(lambda buf, block: buf + block, blocks, bytes())
    assert len(reconst) == input.nbytes
    rcv = memoryview(reconst).cast(input.format)
    assert rcv == input
    a2 = np.frombuffer(reconst, array.dtype)
    assert all(a2 == array)
