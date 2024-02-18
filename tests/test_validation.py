# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

import logging
import os

import numpy as np
import pandas as pd

import pytest

from binpickle import BinPickleFile, dump
from binpickle.errors import FormatError, IntegrityError

_log = logging.getLogger(__name__)


def test_verfy_unsupported_mac(tmp_path, rng: np.random.Generator):
    "Nonzero MAC should fail"
    file = tmp_path / "data.bpk"

    df = pd.DataFrame(
        {
            "key": np.arange(0, 5000),
            "count": rng.integers(0, 1000, 5000),
            "score": rng.normal(10, 2, 5000),
        }
    )

    dump(df, file, codecs=["lz4"])

    # corrupt the file
    stat = os.stat(file)
    _log.info("%s: length %d", file, stat.st_size)
    with open(file, "r+b") as f:
        f.seek(stat.st_size - 4)
        f.write(b"XX")

    # try to read the file
    with pytest.raises(FormatError, match=r"nonzero MACs"):
        with BinPickleFile(file) as _bpf:
            pass


def test_verfy_index(tmp_path, rng: np.random.Generator):
    "Index hash mismatch should fail"
    file = tmp_path / "data.bpk"

    df = pd.DataFrame(
        {
            "key": np.arange(0, 5000),
            "count": rng.integers(0, 1000, 5000),
            "score": rng.normal(10, 2, 5000),
        }
    )

    dump(df, file, codecs=["lz4"])

    # corrupt the file
    stat = os.stat(file)
    _log.info("%s: length %d", file, stat.st_size)
    with open(file, "r+b") as f:
        f.seek(stat.st_size - 34)
        f.write(b"XX")

    # try to read the file
    with pytest.raises(IntegrityError, match=r"incorrect hash"):
        with BinPickleFile(file) as _bpf:
            pass


def test_verfy_buffer(tmp_path, rng: np.random.Generator):
    "Corrupt buffer should fail hash."
    file = tmp_path / "data.bpk"

    df = pd.DataFrame(
        {
            "key": np.arange(0, 5000),
            "count": rng.integers(0, 1000, 5000),
            "score": rng.normal(10, 2, 5000),
        }
    )

    dump(df, file, codecs=["lz4"])

    # corrupt the file
    stat = os.stat(file)
    _log.info("%s: length %d", file, stat.st_size)
    with open(file, "r+b") as f:
        f.seek(32)
        f.write(b"XXXXXXXX")

    # try to read the file
    with BinPickleFile(file) as bpf:
        with pytest.raises(IntegrityError, match=r"incorrect hash"):
            bpf.load()
