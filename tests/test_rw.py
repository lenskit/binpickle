import itertools as it
from tempfile import TemporaryDirectory
from pathlib import Path
import numpy as np
import pandas as pd

import pytest
from hypothesis import given, assume, settings
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays, scalar_dtypes

from binpickle.read import BinPickleFile, load
from binpickle.write import BinPickler, dump
from binpickle import codecs

RW_CTORS = [BinPickler, BinPickler.mappable, BinPickler.compressed]
RW_CODECS = [st.just(None), st.builds(codecs.GZ)]
if hasattr(codecs, 'Blosc'):
    RW_CTORS.append(lambda f: BinPickler.compressed(f, codecs.Blosc('zstd', 5)))
    RW_CODECS.append(st.builds(codecs.Blosc))
    RW_CODECS.append(st.builds(codecs.Blosc, st.just('zstd')))

RW_CONFIGS = it.product(
    RW_CTORS,
    [False, True]
)
RW_PARAMS = ['writer', 'direct']



@pytest.fixture
def rng():
    return np.random.default_rng()


def test_empty(tmp_path):
    "Write a file with nothing in it"
    file = tmp_path / 'data.bpk'

    with BinPickler(file) as w:
        w._finish_file()

    assert file.stat().st_size == 33

    with BinPickleFile(file) as bpf:
        assert len(bpf.entries) == 0


def test_write_buf(tmp_path, rng: np.random.Generator):
    "Write a file with a single array"
    file = tmp_path / 'data.bpk'

    a = rng.integers(0, 5000, 1024, dtype='i4')

    with BinPickler(file) as w:
        w._write_buffer(a)
        w._finish_file()

    with BinPickleFile(file, direct=True) as bpf:
        assert len(bpf.entries) == 1
        e = bpf.entries[0]
        assert e.dec_length == a.nbytes
        assert e.enc_length == a.nbytes
        b2 = bpf._read_buffer(e)
        assert b2.nbytes == e.dec_length
        a2 = np.frombuffer(b2, dtype='i4')
        assert len(a2) == len(a)
        assert all(a2 == a)
        del a2
        del b2


@settings(deadline=None)
@given(st.lists(st.binary()),
       st.one_of(RW_CODECS))
def test_write_encoded_arrays(tmp_path, arrays, codec):
    file = tmp_path / 'data.bpk'

    with BinPickler.compressed(file, codec) as w:
        for a in arrays:
            w._write_buffer(a)
        w._finish_file()

    with BinPickleFile(file) as bpf:
        assert not bpf.find_errors()
        assert len(bpf.entries) == len(arrays)
        for e, a in zip(bpf.entries, arrays):
            if codec is not None:
                assert e.codec
            assert e.dec_length == len(a)
            dat = bpf._read_buffer(e)
            assert dat == a


def test_pickle_array(tmp_path, rng: np.random.Generator):
    "Pickle a NumPy array"
    file = tmp_path / 'data.bpk'

    a = rng.integers(0, 5000, 1024, dtype='i4')

    with BinPickler(file) as w:
        w.dump(a)

    with BinPickleFile(file) as bpf:
        assert len(bpf.entries) == 2
        a2 = bpf.load()
        assert len(a2) == len(a)
        assert all(a2 == a)


@pytest.mark.parametrize(RW_PARAMS, RW_CONFIGS)
def test_pickle_frame(tmp_path, rng: np.random.Generator, writer, direct):
    "Pickle a Pandas data frame"
    file = tmp_path / 'data.bpk'

    df = pd.DataFrame({
        'key': np.arange(0, 5000),
        'count': rng.integers(0, 1000, 5000),
        'score': rng.normal(10, 2, 5000)
    })

    with writer(file) as w:
        w.dump(df)

    with BinPickleFile(file, direct=direct) as bpf:
        assert not bpf.find_errors()
        df2 = bpf.load()
        print(df2)
        assert all(df2.columns == df.columns)
        for c in df2.columns:
            assert all(df2[c] == df[c])
        del df2


def test_dump_frame(tmp_path, rng: np.random.Generator):
    "Pickle a Pandas data frame"
    file = tmp_path / 'data.bpk'

    df = pd.DataFrame({
        'key': np.arange(0, 5000),
        'count': rng.integers(0, 1000, 5000),
        'score': rng.normal(10, 2, 5000)
    })

    dump(df, file)
    df2 = load(file)

    assert all(df2.columns == df.columns)
    for c in df2.columns:
        assert all(df2[c] == df[c])


@given(arrays(scalar_dtypes(), st.integers(500, 10000)))
def test_compress_many_arrays(tmp_path, a):
    "Pickle random NumPy arrays"
    assume(not any(np.isnan(a)))

    with TemporaryDirectory('.test', 'binpickle') as path:
        file = Path(path) / 'data.bpk'

        with BinPickler.compressed(file) as w:
            w.dump(a)

        with BinPickleFile(file) as bpf:
            assert not bpf.find_errors()
            assert len(bpf.entries) in (1, 2)
            a2 = bpf.load()
            assert len(a2) == len(a)
            assert all(a2 == a)


@given(arrays(scalar_dtypes(), st.integers(500, 10000)))
def test_map_many_arrays(a):
    "Pickle random NumPy arrays"
    assume(not any(np.isnan(a)))
    with TemporaryDirectory('.test', 'binpickle') as path:
        file = Path(path) / 'data.bpk'

        with BinPickler.mappable(file) as w:
            w.dump(a)

        with BinPickleFile(file, direct=True) as bpf:
            assert not bpf.find_errors()
            assert len(bpf.entries) in (1, 2)
            a2 = bpf.load()
            assert len(a2) == len(a)
            assert all(a2 == a)
            del a2
