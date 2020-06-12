"""
Constants and functions defining the binpickle format.
"""

import struct
from typing import NamedTuple
import msgpack

MAGIC = b'BPCK'
MIN_VERSION = 1
DEFAULT_VERSION = 2
MAX_VERSION = 2
HEADER_FORMAT = struct.Struct('!4sHHq')
TRAILER_FORMAT = struct.Struct('!QLL')


class FileHeader(NamedTuple):
    """
    File header for a BinPickle file.  The header is a 16-byte sequence containing the
    magic (``BPCK``) followed by version and offset information:

    1. File version (2 bytes, big-endian). Currently only versions 1 and 2 exist.
    2. Reserved (2 bytes). Set to 0.
    3. File length (8 bytes, big-endian).  Length is signed; if the file length is not known,
       this field is set to -1.
    """
    version: int = DEFAULT_VERSION
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
        if verify and (v > MAX_VERSION or v < MIN_VERSION):
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
    Index entry for a buffer in the BinPickle index.  In the BinPickle file,
    these are saved in MsgPack format in the file index.
    """
    offset: int
    "The position in the file where the buffer begins (bytes)."
    enc_length: int
    "The encoded length of the buffer data in bytes."
    dec_length: int
    "The decoded length of the buffer in bytes."
    checksum: int
    "The Adler-32 checksum of the encoded buffer data."
    content_hash: bytes or None = None
    """
    The SHA1 checksum of the *decoded* buffer data.  In a V1 BinPickle file,
    this will be empty.
    """
    codec: tuple = None
    "The codec used to encode the buffer, or None."

    def to_repr(self):
        "Convert an index entry to its MsgPack-compatible representation"
        repr = dict((k, getattr(self, k)) for k in self._fields)
        if self.content_hash is None:
            del repr['content_hash']
        return repr

    @classmethod
    def from_repr(cls, repr):
        "Convert an index entry from its MsgPack-compatible representation"
        if not isinstance(repr, dict):
            raise TypeError("IndexEntry representation must be a dict")
        return cls(**repr)


class FileIndex:
    """
    Index of a BinPickle file.  This is stored in MsgPack format in the
    BinPickle file.
    """
    def __new__(cls, *args, version=DEFAULT_VERSION, **kwargs):
        if version == 1:
            return super().__new__(FileIndexV1)
        elif version == 2:
            return super().__new__(FileIndexV2)
        else:
            raise ValueError(f'unknown version {version}')

    @classmethod
    def unpack(cls, index, version=DEFAULT_VERSION):
        unpacked = msgpack.unpackb(index)
        if isinstance(unpacked, list):
            return FileIndexV1([IndexEntry.from_repr(r) for r in unpacked], version=1)
        elif isinstance(unpacked, dict) and version >= 2:
            entries = [IndexEntry.from_repr(r) for r in unpacked['entries']]
            bufs = unpacked['buffers']
            return FileIndexV2(entries, bufs, version=version)
        else:
            raise ValueError('unknown index format')

    def __len__(self):
        return len(self._buf_list)


class FileIndexV1(FileIndex):
    """
    Index of a BinPickle file.  This is stored in MsgPack format in the
    BinPickle file.
    """
    def __init__(self, entries=None, version=1):
        assert version == 1
        self._entries = entries if entries is not None else []

    @property
    def buffers(self):
        """
        Return the buffer entries in order.
        """
        return self._entries

    def add_entry(self, hash, entry: IndexEntry = None):
        if entry is None:
            if isinstance(hash, IndexEntry):
                entry = hash
                hash = entry.content_hash
            else:
                raise RuntimeError('Version 1 does not support deduplication')
        self._entries.append(entry)

    def pack(self):
        return msgpack.packb([b.to_repr() for b in self.buffers])

    def __len__(self):
        return len(self._entries)


class FileIndexV2(FileIndex):
    """
    Index of a BinPickle file.  This is stored in MsgPack format in the
    BinPickle file.
    """
    def __init__(self, entries=None, buffers=None, version=2):
        assert version == 2
        if entries is None:
            self._entries = {}
            self._buf_list = []
        else:
            self._entries = dict((e.content_hash, e) for e in entries)
            self._buf_list = buffers

    @property
    def buffers(self):
        """
        Return the buffer entries in order.
        """
        return [self._entries[h] for h in self._buf_list]

    def add_entry(self, hash, entry: IndexEntry=None):
        if entry is not None and entry.content_hash is None:
            raise ValueError('V2 index requires content hashes')
        if entry is not None:
            self._entries[hash] = entry
        self._buf_list.append(hash)

    def pack(self):
        return msgpack.packb({
            'entries': list(e.to_repr() for e in self._entries.values()),
            'buffers': self._buf_list
        })

    def __len__(self):
        return len(self._buf_list)
