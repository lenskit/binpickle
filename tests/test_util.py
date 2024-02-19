# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT
# pyright: basic

import hypothesis.strategies as st
from hypothesis import given

from binpickle.write import _align_pos


@given(st.integers(100, 10000000))
def test_align(n: int):
    res = _align_pos(n, 1024)
    assert res >= n
    assert res % 1024 == 0
