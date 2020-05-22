import zlib

from ._base import Codec


class GZ(Codec):
    """
    Zlib (gzip-compatible) codec.
    """

    NAME = 'gz'

    def __init__(self, level=9):
        self.level = level

    def encode(self, buf):
        return zlib.compress(buf, self.level)

    def encode_to(self, buf, out):
        # We have to encode by chunks
        out.write(self.encode(buf))

    def decode(self, buf):
        return zlib.decompress(buf)

    def decode_to(self, buf, out):
        out[:] = self.decode(buf)

    def config(self):
        return {
            'level': self.level
        }
