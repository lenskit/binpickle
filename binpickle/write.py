import os
import mmap
import warnings
import logging
import io
import mmap
from zlib import adler32
import msgpack

from .compat import pickle
from .format import *

_log = logging.getLogger(__name__)


def _align_pos(pos, size=mmap.PAGESIZE):
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

    Args:
        filename(str or pathlib.Path):
            The path to the file to write.
        align(bool):
            If ``True``, align buffers to the page size.
    """

    def __init__(self, filename, *, align=False):
        self.filename = filename
        self.align = align
        self._file = open(filename, 'wb')
        self.entries = []

        self._init_header()

    def dump(self, obj):
        "Dump an object to the file. Can only be called once."
        bio = io.BytesIO()
        pk = pickle.Pickler(bio, protocol=pickle.HIGHEST_PROTOCOL,
                            buffer_callback=self._write_buffer)
        pk.dump(obj)
        buf = bio.getbuffer()
        _log.info('pickled %d bytes with %d buffers', buf.nbytes, len(self.entries))
        self._write_buffer(buf)
        self._finish_file()

    def close(self):
        "Close the bin pickler."
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def _init_header(self):
        pos = self._file.tell()
        if pos > 0:
            warnings.warn('BinPickler not at beginning of file')
        h = FileHeader()
        _log.debug('initializing header for %s', self.filename)
        self._file.write(h.encode())
        assert self._file.tell() == pos + 16

    def _write_buffer(self, buf):
        mv = memoryview(buf)
        offset = self._file.tell()

        if self.align:
            off2 = _align_pos(offset)
            if off2 > offset:
                nzeds = off2 - offset
                zeds = b'\x00' * nzeds
                self._file.write(zeds)
                assert self._file.tell() == off2
                offset = off2

        length = mv.nbytes
        cksum = adler32(mv)

        _log.debug('writing %d bytes at position %d', length, offset)
        self._file.write(mv)
        assert self._file.tell() == offset + length

        self.entries.append(IndexEntry(offset, length, length, cksum))

    def _write_index(self):
        buf = msgpack.packb([e.to_repr() for e in self.entries])
        pos = self._file.tell()
        nbs = len(buf)
        _log.debug('writing %d index entries (%d bytes) at position %d',
                    len(self.entries), nbs, pos)
        self._file.write(buf)
        ft = FileTrailer(pos, nbs, adler32(buf))
        self._file.write(ft.encode())
        return ft

    def _finish_file(self):
        self._write_index()

        pos = self._file.tell()
        _log.debug('finalizing file with length %d', pos)
        h = FileHeader(length=pos)
        self._file.seek(0)
        self._file.write(h.encode())
        self._file.flush()
