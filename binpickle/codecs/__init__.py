"""
Codecs for encoding and decoding buffers in BinPickle.

This is similar in spirit to numcodecs_, but automatically handles some cases
such as splitting arrays into blocks.

.. _numcodecs: https://numcodecs.readthedocs.io/en/stable/
"""

from ._base import Codec  # noqa: F401
from .null import Null
from .gz import GZ
from .blosc import Blosc
from .numcodecs import NC

CODECS = {}


def register(cls):
    CODECS[cls.NAME] = cls


register(Null)
register(GZ)
if Blosc.AVAILABLE:
    register(Blosc)
if NC.AVAILABLE:
    register(NC)


def make_codec(codec, *, null_as_none=False):
    """
    Resolve a codec into a BinPickle-compatible codec.

    Args:
        codec(obj):
            The codec to resolve into a codec.  Can be one of:

            * ``None`` (returns :class:`Null`)
            * A :class:`Codec` object (returned as-is)
            * A string (look up codec by name and return with default options)
            * A :class:`numcodecs.abc.Codec` (wrapped in :class:`NC` and returned)

    Returns:
        Codec: the codec.
    """
    if codec is None and not null_as_none:
        return Null()
    elif isinstance(codec, str):
        return CODECS[codec]()
    elif numcodecs.is_numcodec(codec):
        return NC(codec)
    elif isinstance(codec, Null) and null_as_none:
        return None
    else:
        return codec


def get_codec(name, config):
    """
    Get a codec by name and configuration (as stored in the BinPickle manifest).

    Args:
        name(str or None): the codec name.
        config: the codec configuration, as returned by :meth:`Codec.config`.

    Returns:
        Codec: the configured codec.
    """
    if name is None:
        return Null()
    elif name in CODECS:
        return CODECS[name](**config)
    else:
        raise ValueError(f'unknown codec {name}')
