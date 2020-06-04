import logging
import msgpack
from importlib.util import find_spec

from ._base import Codec


DEFAULT_BLOCKSIZE = 1024 * 1024 * 1024
_log = logging.getLogger(__name__)


def _split_blocks(buf, blocksize):
    if buf.itemsize > 1:
        buf = buf.cast('B')
    length = buf.nbytes
    chunks = []
    for start in range(0, length, blocksize):
        end = start + blocksize
        if end > length:
            end = length
        chunks.append(buf[start:end])

    if not chunks:
        chunks.append(memoryview(b''))
    return chunks


class Blosc(Codec):
    """
    Blosc codec.
    """

    NAME = 'blosc'
    AVAILABLE = find_spec('blosc') is not None

    def __init__(self, name='blosclz', level=9,
                 shuffle=1, blocksize=DEFAULT_BLOCKSIZE):
        if not self.AVAILABLE:
            raise ImportError('blosc is not available')
        self.name = name
        self.level = level
        self.shuffle = shuffle
        self.blocksize = blocksize

    def encode_to(self, buf, out):
        # We have to encode by chunks
        import blosc
        pack = msgpack.Packer()
        mv = memoryview(buf)
        _log.debug('encoding %d bytes (itemsize=%d, format=%s)',
                   mv.nbytes, mv.itemsize, mv.format)
        _log.debug('splitting with block size %d', self.blocksize)
        blocks = _split_blocks(mv, self.blocksize)
        out.write(pack.pack_array_header(len(blocks)))
        for block in blocks:
            assert block.nbytes <= self.blocksize
            comp = blosc.compress(block, cname=self.name, clevel=self.level,
                                  shuffle=self.shuffle, typesize=mv.itemsize)
            out.write(pack.pack(comp))
            block.release()

    def decode_to(self, buf, out):
        import blosc
        blocks = msgpack.unpackb(buf, use_list=True)
        pos = 0
        for block in blocks:
            dec = blosc.decompress(block)
            dmv = memoryview(dec)  # to reduce copies
            n = len(dec)
            e1 = min(pos + n, len(out))
            n1 = e1 - pos
            out[pos:e1] = dmv[:n1]
            if n1 < n:
                out.extend(dmv[n1:])
            pos += n
        if len(out) > pos:
            del out[pos:]

    def config(self):
        return {
            'name': self.name,
            'level': self.level,
            'shuffle': self.shuffle
        }
