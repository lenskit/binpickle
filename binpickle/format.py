# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

"""
Constants and functions defining the binpickle format.
"""

from __future__ import annotations

import enum
import io
import struct
from dataclasses import dataclass, field, fields
from typing import Any, TypeAlias

from binpickle.errors import FormatError

CodecSpec: TypeAlias = dict[str, str | bool | int | float | None]
"""
Type of codec specification dictionaries, to be passed to
:func:`numcodecs.registry.get_codec`.
"""

BufferTypeInfo: TypeAlias = tuple[str, str, tuple[int, ...]]
"""
Type of buffer type (and size/shape) information.
"""

MAGIC = b"BPCK"
VERSION = 2
HEADER_FORMAT = struct.Struct("!4sHHq")
TRAILER_FORMAT = struct.Struct("!QL32s")


class Flags(enum.Flag):
    """
    Flags that can be set in the BinPickle header.
    """

    BIG_ENDIAN = 1
    """
    This file was created on a big-endian system; if absent, the data is in little-endian.

    Note that this affects only the serialized buffer data; it does **not** affect the lengths
    and offsets in the file format, which are always stored in network byte order (big-endian)
    or encoded with MsgPack.
    """

    MAPPABLE = 2
    """
    This file is designed to be memory-mapped.
    """


@dataclass
class FileHeader:
    """
    File header for a BinPickle file.  The header is a 16-byte sequence containing the
    magic (``BPCK``) followed by version and offset information:

    1. File version (2 bytes, big-endian).
    2. Flags (2 bytes), as defined in :class:`Flags`.
    3. File length (8 bytes, big-endian).  Length is signed; if the file length is not known,
       this field is set to -1.
    """

    SIZE = HEADER_FORMAT.size

    version: int = VERSION
    "The NumPy file version."
    flags: Flags = Flags(0)
    length: int = -1
    "The length of the file (-1 for unknown)."

    def encode(self):
        "Encode the file header as bytes."
        return HEADER_FORMAT.pack(MAGIC, self.version, self.flags._value_, self.length)

    @classmethod
    def decode(cls, buf: bytes | bytearray | memoryview, *, verify: bool = True) -> FileHeader:
        """
        Decode a file header from bytes.

        Args:
            buf:
                Buffer contianing the file header to decode.
            verify:
                Whether to fail on invalid header data (such as mismatched magic
                or unsupported version).
        """
        if len(buf) != HEADER_FORMAT.size:
            raise FormatError("incorrect header length")

        m, v, flags, off = HEADER_FORMAT.unpack(buf)
        if verify and m != MAGIC:
            raise FormatError("invalid magic {}".format(m))
        if verify and v != VERSION:
            raise FormatError("invalid version {}".format(v))
        try:
            flags = Flags(flags)
        except ValueError as e:
            raise FormatError("unsupported flags", e)
        return cls(v, flags, off)

    @classmethod
    def read(cls, file: io.FileIO | io.BufferedReader, **kwargs: bool) -> FileHeader:
        buf = file.read(HEADER_FORMAT.size)
        return cls.decode(buf, **kwargs)

    def trailer_pos(self):
        "Get the position of the start of the file trailer."
        if self.length >= HEADER_FORMAT.size + TRAILER_FORMAT.size:
            return self.length - TRAILER_FORMAT.size
        elif self.length > 0:
            raise FormatError("file size {} not enough for BinPickle".format(self.length))
        else:
            return None  # We do not know the file size


@dataclass
class FileTrailer:
    """
    File trailer for a BinPickle file.  The trailer is a 44-byte sequence that tells the
    reader where to find the rest of the binpickle data.  It consists of the following
    fields:

    1. Index start (8 bytes, big-endian).  Measured in bytes from the start of the file.
    2. Index length (4 bytes, big-endian). The number of bytes in the index.
    3. Index digest (32 bytes). The SHA256 digest of the index data.
    """

    SIZE = TRAILER_FORMAT.size

    offset: int
    "Position of the start of the file index."
    length: int
    "Length of the file index."
    hash: bytes
    "SHA-256 digest of the file index."

    def encode(self):
        "Encode the file trailer as bytes."
        return TRAILER_FORMAT.pack(self.offset, self.length, self.hash)

    @classmethod
    def decode(cls, buf: bytes | bytearray | memoryview, *, verify: bool = True) -> FileTrailer:
        """
        Decode a file trailer from bytes.

        Args:
            buf: Buffer containing the trailer to decode.
            verify: Whether to verify invalid trailer data (currently ignored).
        """
        off, len, ck = TRAILER_FORMAT.unpack(buf)
        return cls(off, len, ck)


@dataclass
class IndexEntry:
    """
    Index entry for a buffer in the BinPickle index.
    """

    offset: int
    "The position in the file where the buffer begins (bytes)."
    enc_length: int
    "The encoded length of the buffer data in bytes."
    dec_length: int
    "The decoded length of the buffer in bytes."
    hash: bytes
    "The SHA-256 checksum of the encoded buffer data."
    info: BufferTypeInfo | None
    "Type information for the buffer (if available)."
    codecs: list[CodecSpec] = field(default_factory=list)
    "The sequence of codecs used to encode the buffer."

    def to_repr(self):
        "Convert an index entry to its MsgPack-compatible representation"
        return dict((f.name, getattr(self, f.name)) for f in fields(self))

    @classmethod
    def from_repr(cls, repr: dict[str, Any]):
        "Convert an index entry from its MsgPack-compatible representation"
        if not isinstance(repr, dict):
            raise TypeError("IndexEntry representation must be a dict")
        return cls(**repr)
