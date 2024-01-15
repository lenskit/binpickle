# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

"""
Internal utility functions for Binpickle.
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional

from typing_extensions import Buffer

naturalsize: Optional[Any]

try:
    from humanize import naturalsize
except ImportError:
    naturalsize = None


def human_size(bytes: int | float) -> str:
    if naturalsize:
        return naturalsize(bytes, binary=True, format="%.2f")
    else:
        return "{:.2f} MiB".format(bytes / (1024 * 1024))


def hash_buffer(buf: Buffer) -> bytes:
    if not isinstance(buf, memoryview):
        buf = memoryview(buf)

    return hashlib.sha256(buf).digest()
