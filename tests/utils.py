"""
Test utilities.
"""

import pandas as pd
import numpy as np

from hypothesis import assume, settings
import hypothesis.strategies as st
import hypothesis.extra.numpy as nph


expensive = settings(max_examples=10, deadline=None)


@st.composite
def dataframes(draw, duplicate=False):
    n = draw(st.integers(1, 10000))
    df = pd.DataFrame({
        'key': np.arange(0, n),
        'count': draw(nph.arrays(np.int32, n)),
        'score': draw(nph.arrays(np.float64, n))
    })
    assume(not df['score'].isna().any())
    if duplicate:
        df['s2'] = df['score']
    return df
