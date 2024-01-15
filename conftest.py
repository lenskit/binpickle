# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

from hypothesis import settings
import pytest
import numpy as np


@pytest.fixture
def rng():
    return np.random.default_rng()


# set up profiles
settings.register_profile("default", deadline=1000)
settings.register_profile("large", max_examples=5000)
settings.register_profile("fast", max_examples=10)
settings.load_profile("default")
