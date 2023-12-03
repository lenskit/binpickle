"""
Internal utility functions for Binpickle.
"""
from __future__ import annotations
from typing import Optional, Any
import hashlib
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
