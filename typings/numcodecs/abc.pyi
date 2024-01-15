# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any

from typing_extensions import Buffer, Optional, Self

class Codec(ABC):
    codec_id: Optional[str]

    def encode(self, buf: Buffer) -> Buffer: ...
    def decode(self, buf: Buffer, out: Optional[Buffer] = None) -> Buffer: ...
    def get_config(self) -> dict[str, Any]: ...
    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> Self: ...
