"""
Internal utility functions for Binpickle.
"""

try:
    from natural.size import binarysize
except ImportError:
    binarysize = None


def human_size(bytes):
    if binarysize:
        return binarysize(bytes)
    else:
        return "{:.2f} MiB".format(bytes / (1024 * 1024))
