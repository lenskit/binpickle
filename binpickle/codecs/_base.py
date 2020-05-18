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

    def decode(self, buf):
        """
        Decode a buffer.

        Args:
            buf(bytes-like): the buffer to decode.

        Returns:
            bytes-like: the decoded data
        """

        out = bytearray()
        self.decode_to(buf, out)
        return out

    @abstractmethod
    def decode_to(self, buf, out):
        """
        Decode a buffer into a bytearray.

        Args:
            buf(bytes-like): the buffer to decode.
            out(bytearray):
                the bytearray to receive the output.  This method will resize the
                bytearray as needed to accomodate the output.
        """
