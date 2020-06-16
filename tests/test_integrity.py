from tempfile import TemporaryDirectory
from pathlib import Path
from mmap import mmap

import pandas as pd
import numpy as np

import pytest
from hypothesis import given, assume, settings
import hypothesis.strategies as st
import hypothesis.extra.numpy as nph
import hypothesis.extra.pandas as pdh

from binpickle import dump, BinPickleFile, BinPickler

from test_rw import RW_CODECS

MODES = st.one_of(RW_CODECS + [st.just('mappable')])
PANDAS_DATA = pdh.data_frames(pdh.columns(5, dtype='i4'))
SHAPES = st.one_of(st.integers(1, 1000000), st.tuples(st.integers(1, 1000), st.integers(1, 1000)))
NP_DATA = nph.arrays(st.one_of(nph.integer_dtypes(), nph.floating_dtypes()), SHAPES)
NP_DATA = NP_DATA.filter(lambda x: not np.any(np.isnan(x)))
DATA = st.one_of(NP_DATA, PANDAS_DATA)


@pytest.mark.skip('too slow')
@given(DATA, MODES)
def test_clean(data, codec):
    "Verify clean storage."
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / 'data.bpk'
        if codec == 'mappable':
            dump(data, file, mappable=True)
        else:
            dump(data, file, codec=codec)

        with BinPickleFile(file) as bpf:
            assert not bpf.find_errors()
            d2 = bpf.load()
            if isinstance(data, pd.DataFrame):
                assert d2.equals(data)
            else:
                assert np.all(d2 == data)


def test_bad_offset():
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / 'data.bpk'

        # V1 files are easier to manipulate
        # we will write two buffers of 0s, because the checksum of 0s is 0
        with BinPickler(file, version=1) as bp:
            zed = np.zeros(10, dtype='u1')
            bp._write_buffer(zed)
            bp._write_buffer(zed)

            # now we mess up one entry
            e = bp.index._entries[1]
            bp.index._entries[1] = e._replace(offset=e.offset - 10)

            bp._write_index()
            bp._finish_file()

        with BinPickleFile(file) as bpf:
            errs = bpf.find_errors()
            # we have position and, if the bytes are not all-zero, a checksum error
            assert len(errs) == 1
            assert 'before expected start' in errs[0]


@given(st.lists(st.binary(min_size=5), min_size=2, max_size=10), st.data())
def test_bad_checksum_v1(buffers, data):
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / 'data.bpk'

        with BinPickler(file, version=1) as bp:
            for buf in buffers:
                bp._write_buffer(buf)

            # now we mess up one entry
            pos = data.draw(st.integers(0, len(buffers) - 1))
            e = bp.index.buffers()[pos]
            # frob at least one byte
            to_frob = data.draw(st.integers(1, e.enc_length))
            start = data.draw(st.integers(0, e.enc_length - to_frob))
            start = start + e.offset

            bp._write_index()
            bp._finish_file()

        with file.open('r+b') as f, mmap(f.fileno(), 0) as map:
            print(f'frobbing {start} + {to_frob}')
            for i in range(to_frob):
                pos = start + i
                map[pos] = map[pos] ^ 0xFF
            map.flush()

        with BinPickleFile(file) as bpf:
            errs = bpf.find_errors()
            print(errs)
            # we have checksum errors in 1 of them
            assert len(errs) == 1
            assert 'invalid checksum' in errs[0]


@given(st.lists(st.binary(min_size=5), min_size=2, max_size=10), st.data())
def test_bad_checksum_v2(buffers, data):
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / 'data.bpk'

        with BinPickler(file) as bp:
            for buf in buffers:
                bp._write_buffer(buf)

            # now we mess up one entry
            pos = data.draw(st.integers(0, len(buffers) - 1))
            e = bp.index.buffers()[pos]
            # frob at least one byte
            to_frob = data.draw(st.integers(1, e.enc_length))
            start = data.draw(st.integers(0, e.enc_length - to_frob))
            start = start + e.offset

            bp._write_index()
            bp._finish_file()

        with file.open('r+b') as f, mmap(f.fileno(), 0) as map:
            print(f'frobbing {start} + {to_frob}')
            for i in range(to_frob):
                pos = start + i
                map[pos] = map[pos] ^ 0xFF
            map.flush()

        with BinPickleFile(file) as bpf:
            errs = bpf.find_errors()
            print(errs)
            # we have checksum errors in the repeated item
            assert len(errs) == 1
            assert all('invalid checksum' in e for e in errs)
