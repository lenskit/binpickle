import logging

from hypothesis import given
import hypothesis.strategies as st

from binpickle.write import _align_pos

_log = logging.getLogger(__name__)


@given(st.integers(100, 10000000))
def test_align(n):
    res = _align_pos(n, 1024)
    assert res >= n
    assert res % 1024 == 0
