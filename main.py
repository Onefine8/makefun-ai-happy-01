#!/usr/bin/env python3
"""ai-happy-01 entry program: "Lumo the firefly saved you the brightest light".

Ships the bundled artwork ``entry.png`` to the grader output
directory. The artwork is a storybook watercolour of a tiny
firefly called Lumo holding up a jar of the brightest light in
the garden, with a handwritten note for the judge.

The artwork file is a JPEG (the rules allow PNG or JPEG, told
apart by the first bytes, under the name ``entry.png``). This
program only moves bytes: it checks the file is a whole image
inside the size limits, copies it unchanged, then re-reads the
copy and compares hashes. No network, no randomness, no clock,
so two runs always write the same bytes.

Output directory: ``MAKEFUN_OUTPUT_DIR`` when set, otherwise
``/output``.
"""

import hashlib
import json
import os
import struct
import sys

ARTWORK = "entry.png"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ArtworkError(RuntimeError):
    """Raised when the bundled artwork fails a gate check."""


def locate():
    """Return (source, destination) paths for the artwork."""
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, ARTWORK)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return source, os.path.join(out_dir, ARTWORK)


def read_header(path):
    """Return the first 64 KiB of the artwork (enough for headers)."""
    with open(path, "rb") as handle:
        return handle.read(65536)


def kind_of(head):
    """Return 'jpeg' or 'png' from magic bytes, or raise."""
    if head[:3] == JPEG_MAGIC:
        return "jpeg"
    if head[:8] == PNG_MAGIC:
        return "png"
    raise ArtworkError("artwork is neither JPEG nor PNG")


def jpeg_dimensions(head):
    """Return (width, height) from the first JPEG frame header.

    Skips 0xFF fill bytes before each marker, as real encoders
    emit them, and refuses to read past the header buffer.
    """
    pos = 2
    while pos + 9 <= len(head):
        while pos < len(head) and head[pos] == 0xFF:
            pos += 1
        if pos + 9 > len(head):
            break
        marker = head[pos]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 1
            continue
        length = struct.unpack(">H", head[pos + 1:pos + 3])[0]
        if length < 2 or pos + 1 + length > len(head):
            raise ArtworkError("JPEG segment overruns header")
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", head[pos + 4:pos + 8])
            return width, height
        pos += 1 + length
    raise ArtworkError("no JPEG frame header found")


def png_dimensions(head):
    """Return (width, height) from the PNG IHDR chunk."""
    if head[12:16] != b"IHDR":
        raise ArtworkError("artwork has no PNG header")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def is_whole_image(path, kind):
    """Return True when the file ends with its proper end marker."""
    with open(path, "rb") as handle:
        handle.seek(-2, os.SEEK_END)
        tail = handle.read(2)
    if kind == "jpeg":
        return tail == b"\xff\xd9"
    with open(path, "rb") as handle:
        handle.seek(-12, os.SEEK_END)
        tail = handle.read(12)
    return len(tail) == 12 and tail[4:8] == b"IEND"


def inspect(path):
    """Gate-check the artwork; return a dict of its properties."""
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise ArtworkError(f"artwork is {size} bytes, over the 1 MiB limit")
    head = read_header(path)
    kind = kind_of(head)
    if kind == "jpeg":
        width, height = jpeg_dimensions(head)
    else:
        width, height = png_dimensions(head)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise ArtworkError(f"artwork is {width}x{height}, over the 1024 limit")
    if not is_whole_image(path, kind):
        raise ArtworkError("artwork is truncated: no end marker")
    return {"kind": kind, "width": width, "height": height, "bytes": size}


def sha256_file(path):
    """Return the SHA-256 hex digest of a file, streamed."""
    total = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            total.update(chunk)
    return total.hexdigest()


def ship(source, dest):
    """Copy *source* to *dest* byte-for-byte and prove it matches."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with open(source, "rb") as src, open(dest, "wb") as out:
        while True:
            chunk = src.read(65536)
            if not chunk:
                break
            out.write(chunk)
    if os.path.getsize(dest) != os.path.getsize(source):
        raise ArtworkError("copy size mismatch")
    source_hash = sha256_file(source)
    if sha256_file(dest) != source_hash:
        raise ArtworkError("copy hash mismatch")
    return source_hash


def main():
    source, dest = locate()
    info = inspect(source)
    digest = ship(source, dest)
    report = {
        "entry": "Lumo the firefly saved you the brightest light",
        "file": dest,
        "format": info["kind"],
        "width": info["width"],
        "height": info["height"],
        "bytes": info["bytes"],
        "sha256": digest,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
