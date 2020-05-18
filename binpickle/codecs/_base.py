from abc import ABC, abstractmethod
import io

class Codec(ABC):
    """
    Base class for a codec.
    """

    def encode(self, buf):
        """
        Encode a buffer.

        Args:
            buf(bytes-like): the buffer to encode.

        Returns:
            bytes-like: the encoded data
        """
        out = io.BytesIO()
        self.encode_to(buf, out)
        return out.getbuffer()

    @abstractmethod
    def encode_to(self, buf, out):
        """
        Encode a buffer to a binary output stream.

        Args:
            buf(bytes-like): the buffer to encode.
            out(file-like):
                the output stream.  Must have a ``write`` method
                taking a :class:`bytes`.
        """

    @abstractmethod
    def decode(self, buf):
        """
        Decode a buffer.

        Args:
            buf(bytes-like): the buffer to decode.

        Returns:
            bytes-like: the decoded data
        """
