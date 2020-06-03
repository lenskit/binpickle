from importlib.util import find_spec
from ._base import Codec


def is_numcodec(codec):
    "Test whether a codec is a NumCodecs codec."
    if NC.AVAILABLE:
        import numcodecs
        return isinstance(codec, numcodecs.abc.Codec)
    else:
        return False  # if numcodecs aren't available, it can't be one


class NC(Codec):
    """
    NumCodec wrapper.
    """
    NAME = 'numcodec'
    AVAILABLE = find_spec('numcodecs') is not None

    def __init__(self, codec=None, **kwargs):
        if codec is None:
            import numcodecs
            self.codec = numcodecs.get_codec(kwargs)
        else:
            self.codec = codec

    def encode(self, buf):
        return self.codec.encode(buf)

    def encode_to(self, buf, w):
        w.write(self.encode(buf))

    def decode(self, buf):
        return memoryview(self.codec.decode(buf))

    def decode_to(self, buf, out):
        out[:] = self.decode(buf)

    def config(self):
        return self.codec.get_config()
