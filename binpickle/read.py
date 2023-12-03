from dataclasses import dataclass
from enum import Enum
import hashlib
import mmap
import logging
import io
from os import PathLike
from typing import Optional
from typing_extensions import Buffer
import pickle
import msgpack

from binpickle.encode import resolve_codec
from binpickle.errors import BinPickleError, FormatError, IntegrityError

from .format import FileHeader, IndexEntry, FileTrailer
from ._util import hash_buffer

_log = logging.getLogger(__name__)


class FileStatus(Enum):
    MISSING = 0
    INVALID = 1
    BINPICKLE = 2


@dataclass
class BPKInfo:
    status: FileStatus
    size: int

    @property
    def is_valid(self):
        return self.status == FileStatus.BINPICKLE


class BinPickleFile:
    """
    Class representing a binpickle file in memory.

    Args:
        filename(str or pathlib.Path):
            The name of the file to load.
        direct(bool):
            If ``True``, returned objects zero-copy when possible, but cannot
            outlast the :class:`BinPickleFile` instance.  If ``False``, they
            are copied from the file and do not need to be freed before
            :meth:`close` is called.
        verify(bool):
            If ``True`` (the default), verify file checksums while reading.
    """

    filename: str | PathLike
    direct: bool
    verify: bool
    header: FileHeader
    trailer: FileTrailer
    _map: Optional[mmap.mmap]
    _mv: Optional[memoryview]
    _index_buf: Optional[memoryview]
    entries: list[IndexEntry]

    def __init__(self, filename, *, direct: bool = False, verify: bool = True):
        self.filename = filename
        self.direct = direct
        self.verify = verify
        with open(filename, "rb") as bpf:
            self.header = FileHeader.read(bpf)
            self._map = mmap.mmap(bpf.fileno(), self.header.length, access=mmap.ACCESS_READ)
        self._mv = memoryview(self._map)
        self._read_index()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def load(self) -> object:
        """
        Load the object from the binpickle file.
        """
        if not self.entries:
            raise ValueError("empty pickle file has no objects")
        p_bytes = self._read_buffer(self.entries[-1], direct=True)
        _log.debug(
            "unpickling %d bytes and %d buffers", memoryview(p_bytes).nbytes, len(self.entries) - 1
        )

        buf_gen = (self._read_buffer(e) for e in self.entries[:-1])
        up = pickle.Unpickler(io.BytesIO(p_bytes), buffers=buf_gen)
        return up.load()

    @property
    def is_mappable(self) -> bool:
        "Query whether this file can be memory-mapped."
        return all(not e.codecs for e in self.entries)

    def find_errors(self) -> list[str]:
        """
        Verify binpickle data structure validity.  If the file is invalid, returns
        a list of errors.

        Fatal index errors will result in a failure to open the file, so things such as
        invalid msgpack formats in the index won't be detected here.  This method checks
        buffer hashes, offset overlaps, and such.
        """
        errors = []
        assert self._index_buf is not None, "file not loaded"

        i_sum = hashlib.sha256(self._index_buf).digest()
        if i_sum != self.trailer.hash:
            errors.append("index hash mismatch")

        position = 16
        for i, e in enumerate(self.entries):
            if e.offset < position:
                errors.append(f"entry {i}: offset {e.offset} before expected start {position}")
            buf = self._read_buffer(e, direct=True)
            ndec = memoryview(buf).nbytes
            if ndec != e.dec_length:
                errors.append(f"entry {i}: decoded to {ndec} bytes, expected {e.dec_length}")
            cks = hashlib.sha256(self._read_buffer(e, direct=True, decode=False)).digest()
            if cks != e.hash:
                errors.append("entry {i}: invalid digest")

        return errors

    def close(self) -> None:
        """
        Close the BinPickle file.  If the file is in direct mode, all
        retrieved objects and associated views must first be deleted.
        """
        self._index_buf = None
        self._mv = None
        if self._map is not None:
            self._map.close()
            self._map = None

    def _read_index(self) -> None:
        tpos = self.header.trailer_pos()
        if tpos is None:
            raise FormatError("no file length, corrupt binpickle file?")
        assert self._mv is not None, "file not open"

        buf = self._mv[tpos:]
        assert len(buf) == 44
        self.trailer = FileTrailer.decode(buf)

        i_start = self.trailer.offset
        i_end = i_start + self.trailer.length
        self._index_buf = self._mv[i_start:i_end]
        try:
            self._verify_buffer(self._index_buf, self.trailer.hash, "index")
        except Exception as e:
            self._index_buf.release()
            self._index_buf = None
            raise e

        self.entries = [IndexEntry.from_repr(e) for e in msgpack.unpackb(self._index_buf)]
        _log.debug("read %d entries from file", len(self.entries))

    def _read_buffer(
        self, entry: IndexEntry, *, direct: Optional[bool] = None, decode: bool = True
    ) -> Buffer:
        assert self._mv is not None, "file not open"
        assert self._map is not None, "file not open"
        start = entry.offset
        length = entry.enc_length
        end = start + length
        if direct is None:
            direct = self.direct

        buf = self._mv[start:end]
        try:
            self._verify_buffer(buf, entry.hash)
        except Exception as e:
            # make sure we release the buffer, even if it's captured by the stack trace
            buf.release()
            raise e

        _log.debug("decoding %d bytes from %d with %s", length, start, entry.codecs)

        if decode and entry.codecs:
            codecs = [resolve_codec(c) for c in entry.codecs]
            out: Buffer = buf
            for codec in codecs[::-1]:
                out = codec.decode(out)
            return out

        if direct:
            _log.debug("mapping %d bytes from %d", length, start)
            return buf
        else:
            _log.debug("copying %d bytes from %d", length, start)
            return buf.tobytes()

    def _verify_buffer(self, buf: memoryview, hash: bytes, msg: str = "buffer"):
        if self.verify:
            _log.debug("verifying %s", msg)
            bhash = hash_buffer(buf)
            if bhash != hash:
                raise IntegrityError(f"{msg} has incorrect hash, corrupt file?")


def load(file: str | PathLike) -> object:
    """
    Load an object from a BinPickle file.

    Args:
        file(str or pathlib.Path): The file to load.
    """

    with BinPickleFile(file) as bpf:
        return bpf.load()


def file_info(file: str | PathLike) -> BPKInfo:
    """
    Test whether a file is a BinPickle file, and if so, return basic information
    about it.
    """
    try:
        with open(file, "rb") as f:
            info = FileHeader.read(f)
            return BPKInfo(FileStatus.BINPICKLE, info.length)
    except FileNotFoundError:
        return BPKInfo(FileStatus.MISSING, 0)
    except BinPickleError:
        return BPKInfo(FileStatus.INVALID, 0)
