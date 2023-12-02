"""
Internal utility functions for Binpickle.
"""
from __future__ import annotations
from typing import Optional, Any

naturalsize: Optional[Any]

try:
    from humanize import naturalsize
except ImportError:
    naturalsize = None


def human_size(bytes):
    if naturalsize:
        return naturalsize(bytes, binary=True, format="%.2f")
    else:
        return "{:.2f} MiB".format(bytes / (1024 * 1024))
