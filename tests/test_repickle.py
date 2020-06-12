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

from hypothesis import given, assume, settings
import hypothesis.strategies as st
import hypothesis.extra.numpy as nph

from utils import *


def do_repickle(*args):
    opts = docopt(repickle.__doc__, argv=[str(s) for s in args])
    repickle.main(opts)


@expensive
@given(dataframes())
def test_pickle_to_binpickle(df):
    with TemporaryDirectory() as tf:
        tf = Path(tf)

        src = tf / 'df.pkl'
        dst = tf / 'df.bpk'
        df.to_pickle(src)
        do_repickle('-f', 'pickle', '-t', 'binpickle', src, dst)

        assert dst.exists()
        df2 = binpickle.load(dst)

        assert all(df2['key'] == df['key'])
        assert all(df2['count'] == df['count'])
        assert all(df2['score'] == df['score'])


@expensive
@given(dataframes())
def test_binpickle_to_pickle(df):
    with TemporaryDirectory() as tf:
        tf = Path(tf)

        src = tf / 'df.bpk'
        dst = tf / 'df.pkl'
        binpickle.dump(df, src)
        do_repickle('-f', 'binpickle', '-t', 'pickle', src, dst)

        assert dst.exists()
        df2 = pd.read_pickle(dst)

        assert all(df2['key'] == df['key'])
        assert all(df2['count'] == df['count'])
        assert all(df2['score'] == df['score'])
