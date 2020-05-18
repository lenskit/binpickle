"""
Codecs for encoding and decoding buffers in BinPickle.

This is similar in spirit to `numcodecs`_, but automatically handles some cases
such as splitting arrays into blocks.

.. _numcodecs:: https://numcodecs.readthedocs.io/en/stable/
"""

from ._base import Codec
from .null import Null
from .blosc import Blosc

KNOWN_CODECS = [
    Null,
    Blosc
]
