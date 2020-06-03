"""
Codecs for encoding and decoding buffers in BinPickle.

This is similar in spirit to numcodecs_, but automatically handles some cases
such as splitting arrays into blocks.

.. _numcodecs: https://numcodecs.readthedocs.io/en/stable/
"""

from ._base import Codec  # noqa: F401
import logging

from . import null
from . import gz
from . import blosc
from . import numcodecs

_log = logging.getLogger(__name__)

CODECS = {}

Null = null.Null
GZ = gz.GZ
Blosc = blosc.Blosc
NC = numcodecs.NC


def register(cls):
    CODECS[cls.NAME] = cls


def make_codec(codec, *, null_as_none=False, list_is_tuple=False):
    """
    Resolve a codec into a BinPickle-compatible codec.

    Args:
        codec(obj):
            The codec to resolve into a codec.  Can be one of:

            * ``None`` (returns :class:`Null`)
            * A :class:`Codec` object (returned as-is)
            * A string (look up codec by name and return with default options)
            * A tuple ``(name, config)`` (pass to :func:`get_config`)
            * A list (wrapped in :class:`Chain`)
            * A :class:`numcodecs.abc.Codec` (wrapped in :class:`NC` and returned)

    Returns:
        Codec: the codec.
    """
    if codec is None and not null_as_none:
        return Null()
    elif isinstance(codec, str):
        return CODECS[codec]()
    elif isinstance(codec, tuple) or (list_is_tuple and isinstance(codec, list)):
        name, config = codec
        return get_codec(name, config)
    elif isinstance(codec, list):
        return Chain(codec)
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
        _log.debug('configuring %s: %s', name, config)
        return CODECS[name](**config)
    else:
        raise ValueError(f'unknown codec {name}')


from .chain import Chain   # noqa: E402

register(Null)
register(Chain)
register(GZ)
if Blosc.AVAILABLE:
    register(Blosc)
if NC.AVAILABLE:
    register(NC)
