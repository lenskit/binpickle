import pytest

from hypothesis import given
import hypothesis.strategies as st

from binpickle.codecs import *

@pytest.mark.parametrize('codec', KNOWN_CODECS)
@given(st.binary())
def test_codec_roundtrip(codec, bytes):
    "Round-trip a codec"

    c = codec()
    enc = c.encode(bytes)
    dec = c.decode(bytes)
    assert len(dec) == len(enc)
    assert dec == enc
