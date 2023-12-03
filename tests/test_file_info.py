from pathlib import Path

from binpickle import file_info
from binpickle.read import FileStatus
from binpickle.write import dump


def test_missing_file(tmp_path: Path):
    file = tmp_path / "data.bpk"
    info = file_info(file)
    assert info.status == FileStatus.MISSING
    assert not info.is_valid


def test_empty_file(tmp_path: Path):
    file = tmp_path / "data.bpk"
    file.write_bytes(b"")
    info = file_info(file)
    assert info.status == FileStatus.INVALID
    assert not info.is_valid


def test_invalid_file(tmp_path: Path):
    file = tmp_path / "data.bpk"
    file.write_bytes(b"0" * 4096)
    info = file_info(file)
    assert info.status == FileStatus.INVALID
    assert not info.is_valid


def test_valid_file(tmp_path: Path):
    file = tmp_path / "data.bpk"

    dump(None, file)

    info = file_info(file)
    assert info.status == FileStatus.BINPICKLE
    assert info.is_valid
    assert info.size == file.stat().st_size
