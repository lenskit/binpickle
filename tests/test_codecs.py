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
              st.integers(10, 1000000)))
def test_codec_roundtrip_array(codec, data):
    "Round-trip a codec"
    assume(not any(np.isnan(data)))

    c = codec()
    enc = c.encode(data)
    dec = c.decode(enc)
    a2 = np.frombuffer(dec, dtype=data.dtype)
    assert len(a2) == len(data)
    assert all(a2 == data)
