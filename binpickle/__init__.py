"""
Optimized format for pickling binary data.
"""

__version__ = '0.3.1'

from .write import dump, BinPickler    # noqa: F401
from .read import load, BinPickleFile  # noqa: F401
