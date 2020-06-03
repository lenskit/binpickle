from ._base import Codec
from . import make_codec


class Chain(Codec):
    """
    Codec that chains together other codecs in sequence.  The codecs are applied
    in the provided order for encoding, and reverse order for decoding.
    """
    NAME = 'chain'

    def __init__(self, codecs=()):
        self.codecs = [make_codec(c, list_is_tuple=True) for c in codecs]

    def encode(self, buf):
        data = buf
        for codec in self.codecs:
            data = codec.encode(data)
        return data

    def encode_to(self, buf, w):
        w.write(self.encode(buf))

    def decode(self, buf):
        data = buf
        for codec in self.codecs[::-1]:
            data = codec.decode(data)
        return data

    def decode_to(self, buf, out):
        out[:] = self.decode(buf)

    def config(self):
        return {
            'codecs': [(c.NAME, c.config()) for c in self.codecs]
        }
