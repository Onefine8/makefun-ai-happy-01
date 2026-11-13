#!/usr/bin/env python3
"""ai-happy-01 entry program: "First Flight at Sunset".

Ships the bundled artwork ``entry.png`` to the grader output
directory as ``entry.png``.

The program only moves bytes: it reads the artwork next to this
file, checks that it really is a whole PNG of at most 1024x1024,
copies it unchanged, and then re-reads the copy to prove the two
files are identical. No network, no randomness, no clock, so two
runs always write the same bytes.

Output directory: ``MAKEFUN_OUTPUT_DIR`` when set, otherwise
``/output``.
"""

import hashlib
import os
import struct
import sys

ARTWORK = "entry.png"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def paths():
    """Return (source, destination) paths for the artwork."""
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, ARTWORK)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return source, os.path.join(out_dir, ARTWORK)


def png_size(path):
    """Return (width, height) from a PNG header, or raise."""
    with open(path, "rb") as handle:
        head = handle.read(33)
    if head[:8] != PNG_MAGIC:
        raise RuntimeError("artwork is not a PNG file")
    if head[12:16] != b"IHDR":
        raise RuntimeError("artwork has no PNG header")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def digest(path):
    """Return the SHA-256 hex digest of a file, streamed."""
    total = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            total.update(chunk)
    return total.hexdigest()


def png_complete(path):
    """Return True when the file ends with a whole PNG IEND chunk."""
    with open(path, "rb") as handle:
        handle.seek(-12, os.SEEK_END)
        tail = handle.read(12)
    # IEND chunk: 4-byte length (0), "IEND", 4-byte CRC.
    return len(tail) == 12 and tail[4:8] == b"IEND" and tail[:4] == b"\x00\x00\x00\x00"


def deliver(source, dest):
    """Copy *source* to *dest* byte-for-byte and prove it."""
    width, height = png_size(source)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise RuntimeError(f"artwork is {width}x{height}, over the 1024 limit")
    if os.path.getsize(source) > MAX_BYTES:
        raise RuntimeError("artwork is over the 1 MiB limit")
    if not png_complete(source):
        raise RuntimeError("artwork is truncated: no IEND chunk at the end")

    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with open(source, "rb") as src, open(dest, "wb") as out:
        while True:
            chunk = src.read(65536)
            if not chunk:
                break
            out.write(chunk)

    if os.path.getsize(dest) != os.path.getsize(source):
        raise RuntimeError("copy size mismatch")
    if digest(dest) != digest(source):
        raise RuntimeError("copy hash mismatch")
    return os.path.getsize(dest), digest(dest)


def main():
    source, dest = paths()
    size, sha = deliver(source, dest)
    print(f"Wrote {dest} ({size} bytes, sha256 {sha})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
