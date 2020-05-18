import pytest
import numpy as np

from hypothesis import given, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays, integer_dtypes, floating_dtypes

from binpickle.codecs import *

@pytest.mark.parametrize('codec', KNOWN_CODECS)
@given(st.binary())
def test_codec_roundtrip(codec, data):
    "Round-trip a codec"

    c = codec()
    enc = c.encode(data)
    dec = c.decode(enc)
    assert len(dec) == len(data)
    assert dec == data


@pytest.mark.parametrize('codec', KNOWN_CODECS)
@given(arrays(st.one_of(integer_dtypes(), floating_dtypes()),
              st.integers(10, 10000)))
def test_codec_roundtrip_array(codec, data):
    "Round-trip a codec"
    assume(not any(np.isnan(data)))

    c = codec()
    enc = c.encode(data)
    dec = c.decode(enc)
    a2 = np.frombuffer(dec, dtype=data.dtype)
    assert len(a2) == len(data)
    assert all(a2 == data)


@pytest.mark.parametrize('codec', KNOWN_CODECS)
def test_codec_decode_oversize(codec):
    "Test decoding data to an oversized bytearray"
    c = codec()
    data = bytearray(np.random.randn(500))
    out = bytearray(len(data) * 2)
    enc = c.encode(data)
    c.decode_to(enc, out)
    assert len(out) == len(data)
    assert out == data


def test_large_blosc_encode():
    "Test encoding Blosc data that needs to be split"
    c = Blosc(blocksize=4096)

    data = np.random.randn(10000)
    enc = c.encode(data)
    dec = c.decode(enc)
    assert len(enc) < len(dec)  # we should have compressed
    assert len(dec) == data.nbytes
    assert dec == memoryview(data)

    a2 = np.frombuffer(data)
    assert len(a2) == len(data)
    assert all(a2 == data)
