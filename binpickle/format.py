"""
Constants and functions defining the binpickle format.
"""

import struct
from typing import NamedTuple
from abc import ABCMeta, abstractmethod
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

    def __hash__(self):
        return hash((self.offset, self.enc_length, self.dec_length,
                     self.checksum, self.content_hash))


class FileIndex(metaclass=ABCMeta):
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
            return FileIndexV1.from_repr(unpacked, version)
        elif isinstance(unpacked, dict) and version >= 2:
            return FileIndexV2.from_repr(unpacked, version)
        else:
            raise ValueError('unknown index format')

    @abstractmethod
    def buffers(self):
        """
        Return the buffer entries in order, as needed to reconstitute the
        pickled object.  Duplicates are copied in proper positions.
        """
        pass

    @abstractmethod
    def stored_buffers(self):
        """
        Return the actually stored buffer entries in the order they appear
        in the file.  Does not include duplicates.
        """
        pass

    @abstractmethod
    def add_entry(self, hash, entry: IndexEntry = None):
        """
        Add an entry to the index.
        """
        pass

    @abstractmethod
    def pack(self):
        """
        Pack the index into a binary buffer.
        """


class FileIndexV1(FileIndex):
    """
    Index of a BinPickle file.  This is stored in MsgPack format in the
    BinPickle file.
    """
    def __init__(self, entries=None, version=1):
        assert version == 1
        self._entries = entries if entries is not None else []

    def buffers(self):
        return self._entries

    def stored_buffers(self):
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
        return msgpack.packb([b.to_repr() for b in self.buffers()])

    @classmethod
    def from_repr(cls, repr, version):
        return cls([IndexEntry.from_repr(r) for r in repr], version=1)

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

    def buffers(self):
        return [self._entries[h] for h in self._buf_list]

    def stored_buffers(self):
        return list(self._entries.values())

    def add_entry(self, hash, entry: IndexEntry = None):
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

    @classmethod
    def from_repr(cls, repr, version):
        entries = [IndexEntry.from_repr(r) for r in repr['entries']]
        bufs = repr['buffers']
        return cls(entries, bufs, version=version)

    def __len__(self):
        return len(self._buf_list)
