"""
Re-pickle a file.

Usage:
    repickle [options] SRC DST

Options:
    -f FORMAT
        The source format [default: pickle].
    -t FORMAT
        The destination format [default: binpickle].
    -p PROTOCOL
        Protocol version number.
    -v, --verbose
        Output debug logging.
    SRC
        The source file.
    DST
        The destination file.
"""

import warnings
import pathlib
import logging

from natural.size import binarysize
from docopt import docopt

import binpickle
import pickle
if pickle.HIGHEST_PROTOCOL < 5:
    try:
        import pickle5 as pickle
    except ImportError:
        warnings.warn('No pickle5 module, only protocol 4 supported', ImportWarning)

_log = logging.getLogger('binpickle.repickle')


def read_object(src, format):
    src = pathlib.Path(src)
    stat = src.stat()
    _log.info('reading %s file %s', format, src)
    _log.info('input size %s', binarysize(stat.st_size))
    if format == 'pickle':
        with src.open('rb') as f:
            return pickle.load(f)
    elif format == 'binpickle':
        with binpickle.BinPickleFile(src) as bpk:
            return bpk.load()
    else:
        _log.error('invalid source format %s', format)
        raise ValueError('invalid source format ' + format)


def write_object(obj, dst, format, protocol):
    if protocol is not None:
        protocol = int(protocol)
    dst = pathlib.Path(dst)
    _log.info('writing %s file %s', format, dst)
    if format == 'pickle':
        with dst.open('wb') as f:
            pickle.dump(obj, f, protocol=protocol)
    elif format == 'binpickle':
        binpickle.dump(obj, dst)
    else:
        _log.error('invalid destination format %s', format)
        raise ValueError('invalid destination format ' + format)


def main(opts):
    obj = read_object(opts['SRC'], opts['-f'])
    write_object(obj, opts['DST'], opts['-t'], opts['-p'])


if __name__ == '__main__':
    opts = docopt(__doc__)
    level = logging.DEBUG if opts['--verbose'] else logging.INFO
    logging.basicConfig(level=level)
    main(opts)
