# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

from typing import Any

from .abc import Codec

codec_registry: dict[str, Codec]

def get_codec(config: dict[str, Any]) -> Codec: ...
