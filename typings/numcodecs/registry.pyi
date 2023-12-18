from typing import Any

from .abc import Codec

codec_registry: dict[str, Codec]

def get_codec(config: dict[str, Any]) -> Codec: ...
