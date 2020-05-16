import os
import mmap

from .compat import pickle


class BinPickler:
    """
    Save an object into a binary pickle file.  This is like :class:`pickle.Pickler`,
    except it works on file paths instead of byte streams.
    """
