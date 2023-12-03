"""
Support for encoding and decoding.
"""

from __future__ import annotations
from typing import Optional, TypeAlias, Callable, overload
from typing_extensions import Buffer

from numcodecs.abc import Codec
from numcodecs.registry import get_codec

from binpickle.format import CodecSpec

CodecFunc: TypeAlias = Callable[[Buffer], Codec | str | CodecSpec | None]
CodecArg: TypeAlias = Codec | str | CodecSpec | CodecFunc
ResolvedCodec: TypeAlias = Codec | CodecFunc


@overload
def resolve_codec(codec: CodecSpec) -> Codec:
    ...


@overload
def resolve_codec(codec: CodecArg) -> ResolvedCodec:
    ...


@overload
def resolve_codec(codec: CodecArg, buf: Buffer) -> Codec | None:
    ...


def resolve_codec(codec: CodecArg, buf: Optional[Buffer] = None) -> ResolvedCodec | None:
    """
    Resolve a codec arg into an instantiated codec.
    """

    if isinstance(codec, str):
        return resolve_codec({"id": codec})
    elif isinstance(codec, dict):
        return get_codec(codec)
    elif isinstance(codec, Codec):
        return codec
    elif hasattr(codec, "__call__"):
        if buf is None:
            return codec
        else:
            spec = codec(buf)
            if spec is None:
                return None
            else:
                return resolve_codec(spec, buf)
    else:
        raise TypeError(f"invalid codec argument {type(codec)}")
