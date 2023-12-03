import logging
import functools as ft

import numpy as np

from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
import pytest

from binpickle.write import _align_pos

_log = logging.getLogger(__name__)


def _split_blocks(*args):
    blosc = pytest.importorskip("binpickle.codecs.blosc")
    return blosc._split_blocks(*args)


@given(st.integers(100, 10000000))
def test_align(n):
    res = _align_pos(n, 1024)
    assert res >= n
    assert res % 1024 == 0


def test_split_empty_block():
    blocks = _split_blocks(memoryview(b""), 10)
    assert len(blocks) == 1
    assert blocks[0] == b""


def test_split_one_block():
    blocks = _split_blocks(memoryview(b"asdf"), 10)
    assert len(blocks) == 1
    assert blocks[0] == b"asdf"


def test_split_two_blocks():
    blocks = _split_blocks(memoryview(b"asdf"), 2)
    assert len(blocks) == 2
    assert blocks[0] == b"as"
    assert blocks[1] == b"df"
    assert blocks[0].nbytes == 2
    assert blocks[1].nbytes == 2


def test_split_blocks_mismatch():
    blocks = _split_blocks(memoryview(b"asdfg"), 2)
    assert len(blocks) == 3
    assert blocks[0] == b"as"
    assert blocks[0].nbytes == 2
    assert blocks[1] == b"df"
    assert blocks[1].nbytes == 2
    assert blocks[2] == b"g"
    assert blocks[2].nbytes == 1


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.data())
def test_split_blocks(data):
    bs = data.draw(st.integers(8, 4096))
    input = data.draw(st.binary(min_size=bs // 2, max_size=bs * 8))
    _log.info("input size %d, block size %d", len(input), bs)
    blocks = _split_blocks(memoryview(input), bs)
    _log.info("split into %d blocks", len(blocks))
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
    size = data.draw(st.integers(bs // 8, bs * 4))
    array = np.random.randn(size)
    input = memoryview(array)
    _log.info("input size %d (%d bytes), block size %d", len(input), input.nbytes, bs)
    blocks = _split_blocks(memoryview(input), bs)
    _log.info("split into %d blocks", len(blocks))
    assert all(b.nbytes <= bs for b in blocks)
    assert all(len(b) <= bs for b in blocks)
    assert sum(b.nbytes for b in blocks) == input.nbytes
    reconst = ft.reduce(lambda buf, block: buf + block, blocks, bytes())
    assert len(reconst) == input.nbytes
    rcv = memoryview(reconst).cast(input.format)
    assert rcv == input
    a2 = np.frombuffer(reconst, array.dtype)
    assert all(a2 == array)
