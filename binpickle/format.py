"""
Constants and functions defining the binpickle format.
"""

from dataclasses import dataclass, field, fields
import struct
from typing import TypeAlias

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


@dataclass
class FileHeader:
    """
    File header for a BinPickle file.  The header is a 16-byte sequence containing the
    magic (``BPCK``) followed by version and offset information:

    1. File version (2 bytes, big-endian).
    2. Flags (2 bytes). Currently no flags are defined, so this is set to 0.
    3. File length (8 bytes, big-endian).  Length is signed; if the file length is not known,
       this field is set to -1.
    """

    SIZE = HEADER_FORMAT.size

    version: int = VERSION
    "The NumPy file version."
    length: int = -1
    "The length of the file (-1 for unknown)."

    def encode(self):
        "Encode the file header as bytes."
        return HEADER_FORMAT.pack(MAGIC, self.version, 0, self.length)

    @classmethod
    def decode(cls, buf: bytes, *, verify=True):
        "Decode a file header from bytes."
        if len(buf) != HEADER_FORMAT.size:
            raise FormatError("incorrect header length")

        m, v, flags, off = HEADER_FORMAT.unpack(buf)
        if verify and m != MAGIC:
            raise FormatError("invalid magic {}".format(m))
        if verify and v != VERSION:
            raise FormatError("invalid version {}".format(v))
        if verify and flags != 0:
            raise FormatError("unsupported flags")
        return cls(v, off)

    @classmethod
    def read(cls, file, **kwargs):
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
    length: int
    hash: bytes

    def encode(self):
        "Encode the file trailer as bytes."
        return TRAILER_FORMAT.pack(self.offset, self.length, self.hash)

    @classmethod
    def decode(cls, buf, *, verify=True):
        "Decode a file trailer from bytes."
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
    def from_repr(cls, repr):
        "Convert an index entry from its MsgPack-compatible representation"
        if not isinstance(repr, dict):
            raise TypeError("IndexEntry representation must be a dict")
        return cls(**repr)
