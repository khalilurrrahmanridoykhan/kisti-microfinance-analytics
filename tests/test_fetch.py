import hashlib

import pytest

from kisti.fetch import ChecksumError, fetch_file, sha256_of


def make_source(tmp_path, content=b"microfinance"):
    source = tmp_path / "source.bin"
    source.write_bytes(content)
    return source, hashlib.sha256(content).hexdigest()


def entry_for(source, sha256):
    return {"path": "data/real/raw/file.bin", "url": source.as_uri(), "sha256": sha256}


def test_sha256_of_known_content(tmp_path):
    source, expected = make_source(tmp_path)
    assert sha256_of(source) == expected


def test_downloads_then_uses_cache(tmp_path):
    source, sha256 = make_source(tmp_path)
    root = tmp_path / "repo"
    entry = entry_for(source, sha256)

    assert fetch_file(entry, root) == "downloaded"
    assert (root / entry["path"]).read_bytes() == b"microfinance"
    assert fetch_file(entry, root) == "cached"


def test_checksum_mismatch_is_discarded(tmp_path):
    source, _ = make_source(tmp_path)
    root = tmp_path / "repo"
    entry = entry_for(source, "0" * 64)

    with pytest.raises(ChecksumError):
        fetch_file(entry, root)
    assert not (root / entry["path"]).exists()
    assert not (root / (entry["path"] + ".part")).exists()


def test_corrupted_local_file_is_replaced(tmp_path):
    source, sha256 = make_source(tmp_path)
    root = tmp_path / "repo"
    entry = entry_for(source, sha256)
    dest = root / entry["path"]
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"corrupted")

    assert fetch_file(entry, root) == "downloaded"
    assert dest.read_bytes() == b"microfinance"
