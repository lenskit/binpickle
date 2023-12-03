from .abc import Codec

codec_registry: dict[str, Codec]

def get_codec(config: dict) -> Codec: ...
