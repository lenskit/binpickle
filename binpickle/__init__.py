"""
Optimized format for pickling binary data.
"""

__version__ = '0.3.4'

from .write import dump, BinPickler    # noqa: F401
from .read import load, BinPickleFile  # noqa: F401
