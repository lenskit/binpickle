import mmap
import warnings
import logging
import io
from zlib import adler32
import msgpack

from .compat import pickle
from .format import FileHeader, FileTrailer, IndexEntry
from . import codecs

_log = logging.getLogger(__name__)


def _align_pos(pos, size=mmap.PAGESIZE):
    "Advance a position to be aligned."
    rem = pos % size
    if rem:
        return pos + (size - rem)
    else:
        return pos


class CKOut:
    """
    Wrapper for binary output that computes checksums and sizes on the fly.
    """

    def __init__(self, base):
        self.bytes = 0
        self.checksum = 1
        self.delegate = base

    def write(self, data):
        # get a memory view so we have a portable count of bytes
        mv = memoryview(data)
        self.bytes += mv.nbytes
        self.checksum = adler32(data, self.checksum)
        return self.delegate.write(data)

    def flush(self):
        self.delegate.flush()


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

    def __init__(self, filename, *, align=False, codec=None):
        self.filename = filename
        self.align = align
        self._file = open(filename, 'wb')
        self.entries = []
        self.codec = codec

        self._init_header()

    @classmethod
    def mappable(cls, filename):
        "Convenience method to construct a pickler for memory-mapped use."
        return cls(filename, align=True)

    @classmethod
    def compressed(cls, filename, codec=codecs.GZ()):
        "Convenience method to construct a pickler for compressed storage."
        return cls(filename, codec=codec)

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

    def _encode_buffer(self, buf, out):
        if self.codec is None:
            out.write(buf)
            return None
        elif hasattr(self.codec, '__call__'):
            # codec is callable, call it to get the codec
            codec = self.codec(buf)
            codec = codecs.make_codec(codec)
        else:
            codec = codecs.make_codec(self.codec)

        codec.encode_to(buf, out)
        return (codec.NAME, codec.config())

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

        _log.debug('writing %d bytes at position %d', length, offset)
        cko = CKOut(self._file)
        c_spec = self._encode_buffer(buf, cko)
        _log.debug('encoded %d bytes to %d (%.2f%% saved)', length, cko.bytes,
                   (length - cko.bytes) / length * 100 if length else -0.0)
        _log.debug('used codec %s', c_spec)

        assert self._file.tell() == offset + cko.bytes

        self.entries.append(IndexEntry(offset, cko.bytes, length, cko.checksum,
                                       c_spec))

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


def dump(obj, file, *, mappable=False, codec=codecs.GZ()):
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
        codec(codecs.Codec):
            The codec to use to compress the data, when not saving for
            memory-mapping.
    """

    if mappable:
        bpk = BinPickler(file, align=True)
    else:
        bpk = BinPickler(file, align=False, codec=codec)
    with bpk:
        bpk.dump(obj)
