import pytest
import numpy as np

from hypothesis import given, assume, settings
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays, integer_dtypes, floating_dtypes

from binpickle.codecs import *
if NC.AVAILABLE:
    from numcodecs import LZ4, LZMA

KNOWN_CODECS = [c for c in CODECS.values() if c.NAME != 'numcodec']  # exclude numcodec from common tests

need_blosc = pytest.mark.skipif(not Blosc.AVAILABLE, reason='Blosc not available')
need_numcodecs = pytest.mark.skipif(not NC.AVAILABLE, reason='numcodecs not available')


def test_make_codec_none():
    assert isinstance(make_codec(None), Null)


def test_make_codec_null_str():
    assert isinstance(make_codec('null'), Null)


def test_make_codec_gz_str():
    assert isinstance(make_codec('gz'), GZ)


def test_make_codec_return():
    codec = GZ()
    assert make_codec(codec) is codec


@need_numcodecs
def test_make_codec_wrap():
    inner = LZ4()
    codec = make_codec(inner)
    assert isinstance(codec, NC)
    assert codec.codec is inner


def test_make_codec_to_none():
    "Test internal-use none codec"
    assert make_codec(None, null_as_none=True) is None
    assert make_codec(Null(), null_as_none=True) is None


def test_get_null_with_none():
    codec = get_codec(None, {})
    assert isinstance(codec, Null)


def test_get_null():
    codec = get_codec('null', {})
    assert isinstance(codec, Null)


def test_get_gz():
    codec = get_codec('gz', {})
    assert isinstance(codec, GZ)
    assert codec.level == 9


def test_get_gz_level():
    codec = get_codec('gz', {'level': 5})
    assert isinstance(codec, GZ)
    assert codec.level == 5


@need_blosc
def test_get_blosc():
    codec = get_codec('blosc', {})
    assert isinstance(codec, Blosc)
    assert codec.level == 9


@need_blosc
def test_get_blosc_lvl():
    codec = get_codec('blosc', {'name': 'zstd', 'level': 5})
    assert isinstance(codec, Blosc)
    assert codec.name == 'zstd'
    assert codec.level == 5


@pytest.mark.parametrize('codec', KNOWN_CODECS)
@settings(deadline=500)
@given(st.binary())
def test_codec_roundtrip(codec, data):
    "Round-trip a codec"

    c = codec()
    enc = c.encode(data)
    dec = c.decode(enc)
    assert len(dec) == len(data)
    assert dec == data


@pytest.mark.parametrize('codec', KNOWN_CODECS)
@settings(deadline=500)
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


@need_blosc
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


@need_numcodecs
@given(st.binary())
def test_numcodec_roundtrip(data):
    c = NC(LZMA())
    buf = c.encode(data)
    d2 = c.decode(buf)
    assert len(d2) == len(data)
    assert d2 == data


@need_numcodecs
@given(st.binary())
def test_chain(data):
    # Useless but a test
    codec = Chain([LZMA(), GZ()])
    buf = codec.encode(data)
    d2 = codec.decode(buf)

    assert len(d2) == len(data)
    assert d2 == data


@need_numcodecs
def test_chain_config():
    codec = Chain([LZMA(), GZ()])
    assert len(codec.codecs) == 2
    assert isinstance(codec.codecs[0], NC)
    assert isinstance(codec.codecs[1], GZ)

    cfg = codec.config()
    c2 = get_codec(Chain.NAME, cfg)
    assert len(codec.codecs) == 2
    assert isinstance(codec.codecs[0], NC)
    assert isinstance(codec.codecs[1], GZ)


def test_is_not_numcodec():
    assert not numcodecs.is_numcodec(GZ())

@need_numcodecs
def test_is_numcodec():
    assert numcodecs.is_numcodec(LZ4())
