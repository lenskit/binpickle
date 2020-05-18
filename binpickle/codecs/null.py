from ._base import Codec


class Null(Codec):
    """
    Null codec (passthrough).
    """

    def encode(self, buf):
        return buf

    def encode_to(self, buf, out):
        out.write(buf)

    def decode(self, buf):
        return buf
