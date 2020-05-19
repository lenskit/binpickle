"""
Constants and functions defining the binpickle format.
"""

import struct
from typing import NamedTuple

MAGIC = b'BPCK'
VERSION = 1
HEADER_FORMAT = struct.Struct('!4sHHq')
TRAILER_FORMAT = struct.Struct('!QLL')


class FileHeader(NamedTuple):
    """
    File header for a BinPickle file.  The header is a 16-byte sequence containing the
    magic (``BPCK``) followed by version and offset information:

    1. File version (2 bytes, big-endian). Currently only version 1 exists.
    2. Reserved (2 bytes). Set to 0.
    3. File length (8 bytes, big-endian).  Length is signed; if the file length is not known,
       this field is set to -1.
    """
    version: int = VERSION
    "The NumPy file version."
    length: int = -1
    "The length of the file (-1 for unknown)."

    def encode(self):
        "Encode the file header as bytes."
        return HEADER_FORMAT.pack(MAGIC, self.version, 0, self.length)

    @classmethod
    def decode(cls, buf, *, verify=True):
        "Decode a file header from bytes."
        m, v, pad, off = HEADER_FORMAT.unpack(buf)
        if verify and m != MAGIC:
            raise ValueError('invalid magic {}'.format(m))
        if verify and v != VERSION:
            raise ValueError('invalid version {}'.format(v))
        if verify and pad != 0:
            raise ValueError('invalid padding')
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
            raise ValueError('file size {} not enough for BinPickle'.format(self.length))
        else:
            return None  # We do not know the file size


class FileTrailer(NamedTuple):
    """
    File trailer for a BinPickle file.  The trailer is a 16-byte sequence that tells the
    reader where to find the rest of the binpickle data.  It consists of the following
    fields:

    1. Index start (8 bytes, big-endian).  Measured in bytes from the start of the file.
    2. Index length (4 bytes, big-endian). The number of bytes in the index.
    3. Index checksum (4 bytes, big-endian). The Adler32 checksum of the index data.
    """

    offset: int
    length: int
    checksum: int

    def encode(self):
        "Encode the file trailer as bytes."
        return TRAILER_FORMAT.pack(self.offset, self.length, self.checksum)

    @classmethod
    def decode(cls, buf, *, verify=True):
        "Decode a file trailer from bytes."
        o, l, c = TRAILER_FORMAT.unpack(buf)
        return cls(o, l, c)


class IndexEntry(NamedTuple):
    """
    Index entry for a buffer in the BinPickle index.
    """
    offset: int
    "The position in the file where the buffer begins (bytes)."
    enc_length: int
    "The encoded length of the buffer data in bytes."
    dec_length: int
    "The decoded length of the buffer in bytes."
    checksum: int
    "The Adler-32 checksum of the encoded buffer data."
    codec: tuple = None
    "The codec used to encode the buffer, or None."

    def to_repr(self):
        "Convert an index entry to its MsgPack-compatible representation"
        return dict((k, getattr(self, k)) for k in self._fields)

    @classmethod
    def from_repr(cls, repr):
        "Convert an index entry from its MsgPack-compatible representation"
        if not isinstance(repr, dict):
            raise TypeError("IndexEntry representation must be a dict")
        return cls(**repr)
