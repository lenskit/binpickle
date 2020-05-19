"""
Optimized format for pickling binary data.
"""

__version__ = '0.1'

from .write import dump, BinPickler
from .read import load, BinPickleFile
