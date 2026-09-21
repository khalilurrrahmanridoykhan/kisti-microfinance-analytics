import re

import pytest

from mfi.fetch import ROOT, load_manifest, sha256_of

REQUIRED = {"path", "url", "sha256", "bytes", "description", "publisher", "terms", "retrieved"}


@pytest.fixture(scope="module")
def entries():
    return load_manifest()


def test_manifest_is_not_empty(entries):
    assert entries


def test_every_entry_is_complete(entries):
    for entry in entries:
        assert REQUIRED <= entry.keys(), entry["path"]
        assert entry["url"].startswith("https://"), entry["path"]
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]), entry["path"]
        assert entry["path"].startswith("data/real/raw/"), entry["path"]


def test_paths_are_unique(entries):
    paths = [entry["path"] for entry in entries]
    assert len(paths) == len(set(paths))


def test_local_files_match_the_manifest(entries):
    """Runs on a machine that has already run `make fetch`; skipped in CI, where no PDFs exist."""
    present = [entry for entry in entries if (ROOT / entry["path"]).exists()]
    if not present:
        pytest.skip("source documents not fetched")
    for entry in present:
        assert sha256_of(ROOT / entry["path"]) == entry["sha256"], entry["path"]
