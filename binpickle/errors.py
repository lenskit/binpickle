# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

class BinPickleError(Exception):
    """
    Base class for Binpickle errors.
    """


class FormatError(BinPickleError):
    """
    The Binpickle file is invalid.
    """


class IntegrityError(BinPickleError):
    """
    The Binpickle file failed an integrity check.
    """


class FormatWarning(UserWarning):
    """
    A likely problem has been detected with the file format, but we can proceed
    without correctness errors.
    """
