# pyright: basic
"""
BinPickle CLI internals.
"""
import argparse
import io
import logging
import pickletools
import sys
from textwrap import dedent
from typing import Optional, Sequence

import prettytable as pt

from . import BinPickleFile
from .format import pretty_codec

_log = logging.getLogger(__name__)


def parse_cli(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "binpickle",
        "python -m binpickle [options] FILE",
        dedent(
            """
Print information from a binpickle file.
            """
        ),
    )
    parser.add_argument("FILE", help="the Binpickle file to read.")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging")

    dump = parser.add_argument_group("Dump options")
    dump.add_argument("-l", "--list", action="store_true", help="list the buffers")
    dump.add_argument(
        "-D", "--disassemble", action="store_true", help="disassemble the pickle data"
    )

    return parser.parse_args(args)


def init_cli(opts: argparse.Namespace):
    "Initialize CLI environment (logging, etc.)"
    level = logging.DEBUG if opts.verbose else logging.INFO
    logging.basicConfig(stream=sys.stderr, level=level)


def list_buffers(bpf: BinPickleFile, opts: argparse.Namespace):
    table = pt.PrettyTable()
    table.field_names = ["#", "Length", "Enc. Len.", "Type", "Shape", "Codec"]
    table.align = "r"
    table.align["Type"] = "c"  # pyright: ignore
    table.align["Shape"] = "c"  # pyright: ignore
    table.align["Codec"] = "c"  # pyright: ignore
    table.vrules = pt.NONE
    for i, entry in enumerate(bpf.entries):
        row = [i, entry.dec_length, entry.enc_length]
        if entry.info is None:
            row += ["", ""]
        else:
            at, dt, shape = entry.info
            ss = ", ".join(str(i) for i in shape)
            if at != "ndarray":
                dt = f"{at}[{dt}]"
            row += [dt, ss]

        row.append(pretty_codec(entry.codecs))
        table.add_row(row)

    print(table)


def disassemble_pickle(bpf: BinPickleFile, opts: argparse.Namespace):
    buf = bpf._read_buffer(bpf.entries[-1])
    pickletools.dis(io.BytesIO(buf), sys.stdout)


def main(args: Optional[Sequence[str]] = None):
    opts = parse_cli(args)
    init_cli(opts)

    _log.info("opening %s", opts.FILE)
    with BinPickleFile(opts.FILE) as bpf:
        _log.info("%s: opened file with version %s", opts.FILE, bpf.header.version)
        _log.info("%s: flags: %d (%s)", opts.FILE, bpf.header.flags._value_, bpf.header.flags)
        _log.info("%s: length: %d", opts.FILE, bpf.header.length)
        _log.info("%s: buffers: %d", opts.FILE, len(bpf.entries))

        if opts.list:
            list_buffers(bpf, opts)

        if opts.disassemble:
            disassemble_pickle(bpf, opts)
