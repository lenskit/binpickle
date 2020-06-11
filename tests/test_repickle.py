import pytest
try:
    from docopt import docopt
    from binpickle import repickle
except ImportError:
    pytestmark = pytest.mark.skip('repickle deps not available')

from tempfile import TemporaryDirectory
from pathlib import Path
import binpickle
import pickle

import numpy as np
import pandas as pd

from hypothesis import given, assume
import hypothesis.strategies as st
import hypothesis.extra.numpy as nph

def do_repickle(*args):
    opts = docopt(repickle.__doc__, argv=[str(s) for s in args])
    repickle.main(opts)


@given(st.data())
def test_pickle_to_binpickle(data):
    with TemporaryDirectory() as tf:
        tf = Path(tf)
        n = data.draw(st.integers(1, 10000))
        df = pd.DataFrame({
            'key': np.arange(0, n),
            'count': data.draw(nph.arrays(np.int32, n)),
            'score': data.draw(nph.arrays(np.float64, n))
        })
        assume(not df['score'].isna().any())

        src = tf / 'df.pkl'
        dst = tf / 'df.bpk'
        df.to_pickle(src)
        do_repickle('-f', 'pickle', '-t', 'binpickle', src, dst)

        assert dst.exists()
        df2 = binpickle.load(dst)

        assert all(df2['key'] == df['key'])
        assert all(df2['count'] == df['count'])
        assert all(df2['score'] == df['score'])


@given(st.data())
def test_binpickle_to_pickle(data):
    with TemporaryDirectory() as tf:
        tf = Path(tf)
        n = data.draw(st.integers(1, 10000))
        df = pd.DataFrame({
            'key': np.arange(0, n),
            'count': data.draw(nph.arrays(np.int32, n)),
            'score': data.draw(nph.arrays(np.float64, n))
        })
        assume(not df['score'].isna().any())

        src = tf / 'df.bpk'
        dst = tf / 'df.pkl'
        binpickle.dump(df, src)
        do_repickle('-f', 'binpickle', '-t', 'pickle', src, dst)

        assert dst.exists()
        df2 = pd.read_pickle(dst)

        assert all(df2['key'] == df['key'])
        assert all(df2['count'] == df['count'])
        assert all(df2['score'] == df['score'])
