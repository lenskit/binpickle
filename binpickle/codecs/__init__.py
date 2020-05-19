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


def get_codec(name, config):
    """
    Get a codec by name and configuration.

    Args:
        name(str or None): the codec name.
        config: the codec configuration, as returned by :meth:`Codec.config`.

    Returns:
        Codec: the configured codec.
    """
    if name is None:
        return Null()
    else:
        for c in KNOWN_CODECS:
            if c.NAME == name:
                return c(**config)

        raise ValueError(f'unknown codec {name}')
