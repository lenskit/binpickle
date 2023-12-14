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
