#!/usr/bin/env python3
"""Fetch the frozen per-request corpus from its Zenodo deposit and verify it.

The corpus ships in this repository (data/InferenceCarbon_corpus_frozen_*.zip)
and is mirrored in the Zenodo deposit. This script downloads every file listed
in the Zenodo record and checks its SHA-256 against the manifest (manifest.csv),
so a replicator can prove the corpus they analyse is the corpus that was frozen
- and that the two copies are byte-identical.

Usage:
    python fetch_corpus.py [--record RECORD_ID] [--dest data/corpus]

Requires only the Python standard library. No API key is needed; the deposit
is open access.
"""

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

# Version record of the frozen corpus deposit (DOI 10.5281/zenodo.21840989).
# A version record, not the concept record, so the fetched bytes can never
# silently change. The deposit publishes with the v1.0.0 release; until then
# this id will not resolve.
DEFAULT_RECORD_ID = "21840989"

ZENODO_API = "https://zenodo.org/api/records/{record_id}"
CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, str]:
    with manifest_path.open(newline="") as f:
        return {row["filename"]: row["sha256"].lower() for row in csv.DictReader(f)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", default=DEFAULT_RECORD_ID,
                        help="Zenodo record id of the corpus deposit")
    parser.add_argument("--dest", default=str(Path(__file__).parent / "corpus"),
                        help="download directory (gitignored)")
    parser.add_argument("--manifest", default=str(Path(__file__).parent / "manifest.csv"))
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    if not manifest:
        print("error: manifest.csv is empty — nothing to verify against.", file=sys.stderr)
        return 2

    with urllib.request.urlopen(ZENODO_API.format(record_id=args.record)) as resp:
        record = json.load(resp)

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    files = {f["key"]: f for f in record.get("files", [])}
    missing_remote = sorted(set(manifest) - set(files))
    if missing_remote:
        print(f"error: {len(missing_remote)} manifest file(s) absent from the "
              f"deposit: {', '.join(missing_remote)}", file=sys.stderr)
        return 1

    failures = []
    for name, expected in sorted(manifest.items()):
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not (target.exists() and sha256_of(target) == expected):
            url = files[name]["links"]["self"]
            print(f"fetching {name} ...")
            urllib.request.urlretrieve(url, target)
        actual = sha256_of(target)
        status = "ok" if actual == expected else "CHECKSUM MISMATCH"
        print(f"  {name}: {status}")
        if actual != expected:
            failures.append(name)

    if failures:
        print(f"\nFAILED: {len(failures)} file(s) did not match manifest.csv.",
              file=sys.stderr)
        return 1
    print(f"\nAll {len(manifest)} corpus files fetched and verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
