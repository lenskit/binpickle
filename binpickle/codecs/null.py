from ._base import Codec


class Null(Codec):
    """
    Null codec (passthrough).
    """
    NAME = 'null'

    def encode(self, buf):
        return buf

    def encode_to(self, buf, out):
        out.write(buf)

    def decode(self, buf, length=None):
        return buf

    def decode_to(self, buf, out):
        out[:] = buf

    def config(self):
        return {}
