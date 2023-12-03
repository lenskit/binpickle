import mmap
from os import PathLike
import warnings
import logging
import io
import hashlib
import pickle
import msgpack

from typing_extensions import Buffer, List, Optional, Self

import numpy as np

from .format import CodecSpec, FileHeader, FileTrailer, IndexEntry
from .encode import ResolvedCodec, resolve_codec, CodecArg
from ._util import human_size

_log = logging.getLogger(__name__)


def _align_pos(pos: int, size: int = mmap.PAGESIZE) -> int:
    "Advance a position to be aligned."
    rem = pos % size
    if rem:
        return pos + (size - rem)
    else:
        return pos


class BinPickler:
    """
    Save an object into a binary pickle file.  This is like :class:`pickle.Pickler`,
    except it works on file paths instead of byte streams.

    A BinPickler is also a context manager that closes itself when exited::

        with BinPickler('file.bpk') as bpk:
            bpk.dump(obj)

    Args:
        filename(str or pathlib.Path):
            The path to the file to write.
        align(bool):
            If ``True``, align buffers to the page size.
        codec:
            The codec to use for encoding buffers.  This can be anything that can be
            passed to :func:`binpickle.codecs.make_codec`, or it can be a function
            that takes a buffer and returns the codec to use for that buffer (to
            use different codecs for different types or sizes of buffers).
    """

    filename: str | PathLike
    align: bool
    codecs: list[ResolvedCodec]
    entries: List[IndexEntry]
    _file: io.BufferedWriter

    def __init__(
        self,
        filename: str | PathLike,
        *,
        align=False,
        codecs: Optional[list[CodecArg]] = None,
    ):
        self.filename = filename
        self.align = align
        self._file = open(filename, "wb")
        self.entries = []

        if codecs is None:
            self.codecs = []
        else:
            # pre-resolve the codecs
            self.codecs = [resolve_codec(c) for c in codecs]

        self._init_header()

    @classmethod
    def mappable(cls, filename: str | PathLike):
        "Convenience method to construct a pickler for memory-mapped use."
        return cls(filename, align=True)

    @classmethod
    def compressed(cls, filename: str | PathLike, codec: CodecArg = "gzip"):
        "Convenience method to construct a pickler for compressed storage."
        return cls(filename, codecs=[codec])

    def dump(self, obj: object) -> None:
        "Dump an object to the file. Can only be called once."
        bio = io.BytesIO()
        pk = pickle.Pickler(
            bio, protocol=pickle.HIGHEST_PROTOCOL, buffer_callback=self._write_buffer
        )
        pk.dump(obj)
        buf = bio.getbuffer()

        tot_enc = sum(e.enc_length for e in self.entries)
        tot_dec = sum(e.dec_length for e in self.entries)
        _log.info(
            "pickled %d bytes with %d buffers totaling %s (%s encoded)",
            buf.nbytes,
            len(self.entries),
            human_size(tot_dec),
            human_size(tot_enc),
        )
        self._write_buffer(buf)
        self._finish_file()

    def close(self) -> None:
        "Close the bin pickler."
        self._file.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def _init_header(self) -> None:
        pos = self._file.tell()
        if pos > 0:
            warnings.warn("BinPickler not at beginning of file")
        h = FileHeader()
        _log.debug("initializing header for %s", self.filename)
        self._file.write(h.encode())
        assert self._file.tell() == pos + FileHeader.SIZE

    def _encode_buffer(
        self,
        buf: Buffer,
    ) -> tuple[Buffer, list[CodecSpec]]:
        # fast-path empty buffers
        if memoryview(buf).nbytes == 0:
            return b"", []

        # resolve any deferred codecs
        codecs = [resolve_codec(c, buf) for c in self.codecs]

        for codec in codecs:
            if codec is not None:
                buf = codec.encode(buf)

        return buf, [c.get_config() for c in codecs if c is not None]

    def _write_buffer(self, buf: Buffer) -> None:
        mv = buf.raw() if isinstance(buf, pickle.PickleBuffer) else memoryview(buf)
        offset = self._file.tell()

        if self.align:
            off2 = _align_pos(offset)
            if off2 > offset:
                nzeds = off2 - offset
                zeds = b"\x00" * nzeds
                self._file.write(zeds)
                assert self._file.tell() == off2
                offset = off2

        length = mv.nbytes

        binfo = None
        if isinstance(mv.obj, np.ndarray):
            binfo = ("ndarray", str(mv.obj.dtype), mv.obj.shape)

        _log.debug("writing %d bytes at position %d", length, offset)
        buf, c_spec = self._encode_buffer(buf)
        enc_len = memoryview(buf).nbytes
        _log.debug(
            "encoded %d bytes to %d (%.2f%% saved)",
            length,
            enc_len,
            (length - enc_len) / length * 100 if length else -0.0,
        )
        _log.debug("used codecs %s", c_spec)
        hash = hashlib.sha256(buf)
        _log.debug("has hash %s", hash.hexdigest())
        self._file.write(buf)

        assert self._file.tell() == offset + enc_len

        self.entries.append(IndexEntry(offset, enc_len, length, hash.digest(), binfo, c_spec))

    def _write_index(self) -> FileTrailer:
        buf = msgpack.packb([e.to_repr() for e in self.entries])
        pos = self._file.tell()
        nbs = len(buf)
        _log.debug(
            "writing %d index entries (%d bytes) at position %d", len(self.entries), nbs, pos
        )
        self._file.write(buf)
        hash = hashlib.sha256(buf)
        ft = FileTrailer(pos, nbs, hash.digest())
        self._file.write(ft.encode())
        return ft

    def _finish_file(self) -> None:
        self._write_index()

        pos = self._file.tell()
        _log.debug("finalizing file with length %d", pos)
        h = FileHeader(length=pos)
        self._file.seek(0)
        self._file.write(h.encode())
        self._file.flush()


def dump(obj, file: str | PathLike, *, mappable: bool = False, codecs: list[CodecArg] = ["gzip"]):
    """
    Dump an object to a BinPickle file.  This is a convenience wrapper
    around :class:`BinPickler`.

    To save with default compression for storage or transport::

        dump(obj, 'file.bpk')

    To save in a file optimized for memory-mapping::

        dump(obj, 'file.bpk', mappable=True)

    Args:
        obj: The object to dump.
        file(str or pathlib.Path): The file in which to save the object.
        mappable(bool):
            If ``True``, save for memory-mapping.  ``codec`` is ignored
            in this case.
        codecs:
            The codecs to use to compress the data, when not saving for
            memory-mapping.
    """

    if mappable:
        bpk = BinPickler(file, align=True)
    else:
        bpk = BinPickler(file, align=False, codecs=codecs)
    with bpk:
        bpk.dump(obj)
