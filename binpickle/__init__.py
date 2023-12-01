"""
Optimized format for pickling binary data.
"""

from importlib.metadata import version, PackageNotFoundError

from .write import dump, BinPickler
from .read import load, BinPickleFile

try:
    __version__ = version("progress-api")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = ["dump", "BinPickler", "load", "BinPickleFile"]
