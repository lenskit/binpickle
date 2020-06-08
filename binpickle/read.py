import mmap
import logging
import io
from zlib import adler32
import msgpack

from .compat import pickle
from .format import FileHeader, IndexEntry, FileTrailer
from .codecs import get_codec

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
        with open(filename, 'rb') as bpf:
            self.header = FileHeader.read(bpf)
            self._map = mmap.mmap(bpf.fileno(), self.header.length,
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

    def find_errors(self):
        """
        Verify binpickle data structure validity.  If the file is invalid, returns
        a list of errors.

        Fatal index errors will result in a failure to open the file, so things such as
        invalid msgpack formats in the index won't be detected here.  This method checks
        buffer checksums, offset overlaps, and such.
        """
        errors = []

        i_sum = adler32(self._index_buf)
        if i_sum != self.trailer.checksum:
            errors.append(f'invalid index checksum ({i_sum} != {self.trailer.checksum})')

        position = 16
        for i, e in enumerate(self.entries):
            if e.offset < position:
                errors.append(f'entry {i}: offset {e.offset} before expected start {position}')
            buf = self._read_buffer(e, direct=True)
            ndec = len(buf)
            if ndec != e.dec_length:
                errors.append(f'entry {i}: decoded to {ndec} bytes, expected {e.dec_length}')
            cks = adler32(self._read_buffer(e, direct=True, decode=False))
            if cks != e.checksum:
                errors.append('entry {i}: invalid checksum ({cks} != {e.checksum}')

        return errors

    def close(self):
        """
        Close the BinPickle file.  If the file is in direct mode, all
        retrieved objects and associated views must first be deleted.
        """
        self._index_buf = None
        self._mv = None
        if self._map is not None:
            self._map.close()
            self._map = None

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

    def _read_buffer(self, entry: IndexEntry, *, direct=None, decode=True):
        start = entry.offset
        length = entry.enc_length
        end = start + length
        if direct is None:
            direct = self.direct

        if decode and entry.codec:
            name, cfg = entry.codec
            _log.debug('decoding %d bytes from %d with %s', length, start, name)
            out = bytearray(entry.dec_length)
            codec = get_codec(name, cfg)
            codec.decode_to(self._mv[start:end], out)
            return out
        if direct:
            _log.debug('mapping %d bytes from %d', length, start)
            return self._mv[start:end]
        else:
            _log.debug('copying %d bytes from %d', length, start)
            return self._map[start:end]


def load(file):
    """
    Load an object from a BinPickle file.

    Args:
        file(str or pathlib.Path): The file to load.
    """

    with BinPickleFile(file) as bpf:
        return bpf.load()
