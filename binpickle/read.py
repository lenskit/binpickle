import os
import mmap
import warnings
import logging
import io
from zlib import adler32
import msgpack
import mmap

from .compat import pickle
from .format import *

_log = logging.getLogger(__name__)


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
    """

    def __init__(self, filename, *, direct=False):
        self.filename = filename
        self.direct = direct
        self._file = open(filename, 'rb')
        self.header = FileHeader.read(self._file)
        self._map = mmap.mmap(self._file.fileno(), self.header.length,
                              access=mmap.ACCESS_READ)
        self._mv = memoryview(self._map)
        self._read_index()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def load(self):
        """
        Load the object from the binpickle file.
        """
        if not self.entries:
            raise ValueError('empty pickle file has no objects')
        p_bytes = self._read_buffer(self.entries[-1], direct=True)
        _log.debug('unpickling %d bytes and %d buffers',
                   len(p_bytes), len(self.entries) - 1)

        buf_gen = (self._read_buffer(e) for e in self.entries[:-1])
        up = pickle.Unpickler(io.BytesIO(p_bytes), buffers=buf_gen)
        return up.load()

    def close(self):
        """
        Close the BinPickle file.  If the file is in direct mode, all
        retrieved objects and associated views must first be deleted.
        """
        del self._index_buf
        del self._mv
        self._map.close()
        self._file.close()

    def _read_index(self):
        tpos = self.header.trailer_pos()
        if tpos is None:
            raise ValueError('no file length, corrupt binpickle file?')

        buf = self._mv[tpos:]
        assert len(buf) == 16
        self.trailer = FileTrailer.decode(buf)

        i_start = self.trailer.offset
        i_end = i_start + self.trailer.length
        self._index_buf = self._mv[i_start:i_end]
        self.entries = [IndexEntry.from_repr(e) for e in msgpack.unpackb(self._index_buf)]
        _log.debug('read %d entries from file', len(self.entries))

    def _read_buffer(self, entry: IndexEntry, *, direct=None):
        start = entry.offset
        length = entry.enc_length
        end = start + length
        if direct is None:
            direct = self.direct
        if direct:
            _log.debug('mapping %d bytes from %d', length, start)
            return self._mv[start:end]
        else:
            _log.debug('copying %d bytes from %d', length, start)
            return self._map[start:end]
