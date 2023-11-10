"""
Optimized format for pickling binary data.
"""

__version__ = "0.4.0"

from .write import dump, BinPickler  # noqa: F401
from .read import load, BinPickleFile  # noqa: F401
