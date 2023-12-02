from abc import ABC
from typing import Optional, Self
import numpy

BufferLike = bytes | bytearray | memoryview | numpy.ndarray

class Codec(ABC):
    codec_id: Optional[str]

    def encode(self, buf: BufferLike) -> BufferLike: ...
    def decode(self, buf: BufferLike, out: Optional[BufferLike] = None) -> BufferLike: ...
    def get_config(self) -> dict: ...
    @classmethod
    def from_config(cls, cfg: dict) -> Self: ...
