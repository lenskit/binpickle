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
