#!/usr/bin/env python3
"""ai-happy-01 entry program.

Copies the bundled artwork ``entry.png`` (which sits next to this file)
to the grader output location as ``entry.png``.

The copy is byte-for-byte and fully deterministic: the program performs
no network access, no randomness, no timestamps and no image processing,
so two runs always produce identical output bytes.

Output directory:
    ``MAKEFUN_OUTPUT_DIR`` when set, otherwise ``/output``.
"""

import hashlib
import os
import shutil
import sys

# Name of the artwork file bundled with this program.
SOURCE_NAME = "entry.png"

# Fallback output directory when MAKEFUN_OUTPUT_DIR is not set.
DEFAULT_OUTPUT_DIR = "/output"


def output_dir() -> str:
    """Return the directory the entry image must be written to."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR


def sha256_of(path: str) -> str:
    """Return the SHA-256 hex digest of the file at *path*."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    # The source image lives in the same directory as this script,
    # so the program works no matter where it is invoked from.
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)

    dest_dir = output_dir()
    dest = os.path.join(dest_dir, SOURCE_NAME)

    # Create the output directory if it does not exist yet.
    os.makedirs(dest_dir, exist_ok=True)

    # Byte-for-byte copy: no decoding, no re-encoding, no changes.
    shutil.copyfile(source, dest)

    # Verify the copy landed intact: the output must be exactly as
    # large as the source and byte-identical (same SHA-256 hash),
    # otherwise fail loudly instead of silently submitting a
    # truncated or corrupted image.
    source_size = os.path.getsize(source)
    dest_size = os.path.getsize(dest)
    if dest_size != source_size:
        raise RuntimeError(
            f"size mismatch: source {source_size} bytes, "
            f"output {dest_size} bytes"
        )
    if sha256_of(source) != sha256_of(dest):
        raise RuntimeError("hash mismatch: output is not identical to source")

    print(f"Wrote {dest} ({dest_size} bytes, sha256 {sha256_of(dest)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
