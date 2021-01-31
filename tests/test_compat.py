import sys
from os import fspath
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid
import subprocess as sp
import logging

import pandas as pd
import numpy as np

from hypothesis import given, assume, settings
import hypothesis.strategies as st
import hypothesis.extra.numpy as nph

import binpickle
import pickle

from pytest import fixture, skip

from utils import *
from test_rw import RW_CTORS

_log = logging.getLogger(__name__)
ROOT = Path(__file__).parent.parent


@fixture(scope='session')
def v_prev2():
    git = ROOT / '.git'
    if not git.exists():
        skip('not in a git checkout')

    with TemporaryDirectory(prefix='binpickle-test-') as btf:
        btf = Path(btf)
        wt_dir = btf / 'binpickle-tree'
        _log.info('creating worktree for version 0.3.2 in %s', wt_dir)
        sp.run(['git', 'worktree', 'add', fspath(wt_dir), 'v0.3.2'], check=True)
        shutil.copy(ROOT / 'binpickle' / 'repickle.py', wt_dir / 'repickle.py')
        repickle(wt_dir, '--help')
        yield wt_dir


def repickle(dir, *args):
    cmd = [sys.executable, 'repickle.py'] + [str(s) for s in args]
    sp.run(cmd, check=True, cwd=dir)


@expensive()
@given(dataframes())
def test_read_prev2(v_prev2, obj):
    "Test that we can read a pre-V2 binpickle file."
    tdir = v_prev2.parent

    name = uuid.uuid4()

    src = tdir / f'{name}.pkl'
    dst = tdir / f'{name}.bpk'

    with src.open('wb') as sf:
        _log.info('writing %s', src)
        pickle.dump(obj, sf)

    repickle(v_prev2, '-f', 'pickle', '-t', 'binpickle',
             fspath(src), fspath(dst))

    _log.info('reading %s', dst)
    o2 = binpickle.load(dst)

    assert o2.equals(obj)


@expensive(25)
@given(dataframes(), st.one_of([st.just(c) for c in RW_CTORS]))
def test_write_prev2(v_prev2, obj, ctor):
    "Test that we can write a backwards-compatible V1 binpickle file."
    tdir = v_prev2.parent

    name = uuid.uuid4()

    src = tdir / f'{name}.pkl'
    dst = tdir / f'{name}.bpk'

    with ctor(src, version=1) as bpw:
        bpw.dump(obj)

    repickle(v_prev2, '-f', 'binpickle', '-t', 'pickle',
             fspath(src), fspath(dst))

    _log.info('reading %s', dst)
    with dst.open('rb') as f:
        o2 = pickle.load(f)

    assert o2.equals(obj)
