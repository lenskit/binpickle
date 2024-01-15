# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

"""
Optimized format for pickling binary data.
"""

from importlib.metadata import PackageNotFoundError, version

from .read import BinPickleFile, file_info, load
from .write import BinPickler, dump

try:
    __version__ = version("binpickle")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = ["dump", "BinPickler", "load", "BinPickleFile", "file_info"]
