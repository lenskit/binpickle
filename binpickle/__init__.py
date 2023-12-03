"""
Optimized format for pickling binary data.
"""

from importlib.metadata import version, PackageNotFoundError

from .write import dump, BinPickler
from .read import load, BinPickleFile, file_info

try:
    __version__ = version("binpickle")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = ["dump", "BinPickler", "load", "BinPickleFile", "file_info"]
