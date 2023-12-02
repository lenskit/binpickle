"""
Internal utility functions for Binpickle.
"""

try:
    from humanize import naturalsize
except ImportError:
    naturalsize = None


def human_size(bytes):
    if naturalsize:
        return naturalsize(bytes, binary=True, format="%.2f")
    else:
        return "{:.2f} MiB".format(bytes / (1024 * 1024))
