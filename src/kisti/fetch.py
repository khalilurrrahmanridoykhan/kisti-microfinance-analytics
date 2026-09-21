"""Download the public source documents listed in data/source-manifest.json.

A file is downloaded only if it is missing or its checksum differs, and a download whose
checksum does not match the manifest is discarded, so the raw folder never holds a file
that differs from what the analysis was written against.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "source-manifest.json"
USER_AGENT = "kisti-microfinance-analytics (+https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics)"


class ChecksumError(RuntimeError):
    """A downloaded file did not match the checksum recorded in the manifest."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["files"]


def fetch_file(entry: dict, root: Path = ROOT) -> str:
    """Make sure the file for one manifest entry is present. Returns "cached" or "downloaded"."""
    dest = root / entry["path"]
    if dest.exists() and sha256_of(dest) == entry["sha256"]:
        return "cached"

    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    request = urllib.request.Request(entry["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as out:
        for chunk in iter(lambda: response.read(1 << 20), b""):
            out.write(chunk)

    actual = sha256_of(partial)
    if actual != entry["sha256"]:
        partial.unlink()
        raise ChecksumError(f"{entry['path']}: expected {entry['sha256']}, got {actual}")
    partial.replace(dest)
    return "downloaded"


def main() -> int:
    for entry in load_manifest():
        print(f"{fetch_file(entry):>10}  {entry['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
