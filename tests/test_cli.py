# pyright: basic
from os import fspath
from pathlib import Path
from typing import Generator

import numpy as np
import pandas as pd

from pytest import CaptureFixture, LineMatcher, fixture

from binpickle._cli import main
from binpickle.write import dump


def gen_frame(file: Path, rng: np.random.Generator, mappable: bool = False):
    "Pickle a Pandas data frame"

    df = pd.DataFrame(
        {
            "key": np.arange(0, 5000),
            "count": rng.integers(0, 1000, 5000),
            "score": rng.normal(10, 2, 5000),
        }
    )

    dump(df, file, mappable=mappable)


@fixture
def df_bpf(tmp_path: Path, rng: np.random.Generator) -> Generator[Path, None, None]:
    file = tmp_path / "data.bpk"
    gen_frame(file, rng)

    yield file


def test_no_opts(df_bpf: Path):
    rc = main([fspath(df_bpf)], init_log=False)
    assert rc == 0


def test_list(capsys: CaptureFixture[str], df_bpf: Path):
    capsys.readouterr()
    rc = main(["-l", fspath(df_bpf)], init_log=False)
    assert rc == 0
    out, _err = capsys.readouterr()
    lm = LineMatcher(out.splitlines())
    lm.re_match_lines([r"\s+#\s+Offset.*", r"\s+0\s+\d+\s+\d+\s+\d+.*", r"\s+1\s+\d+\s+\d+.*"])


def test_disassemble(capsys: CaptureFixture[str], df_bpf: Path):
    capsys.readouterr()
    rc = main(["-D", fspath(df_bpf)], init_log=False)
    assert rc == 0
    out, _err = capsys.readouterr()
    lm = LineMatcher(out.splitlines())
    lm.re_match_lines([r"\s+\d+:\s+\\x\w+\s+PROTO\s+5"])


def test_verify(capsys: CaptureFixture[str], df_bpf: Path):
    rc = main(["-V", fspath(df_bpf)], init_log=False)
    assert rc == 0


def test_verify_fail(capsys: CaptureFixture[str], df_bpf: Path):
    # corrupt the file
    with open(df_bpf, "r+b") as f:
        f.seek(32)
        f.write(b"\0\0")

    # run verification
    rc = main(["-V", fspath(df_bpf)], init_log=False)
    assert rc != 0
