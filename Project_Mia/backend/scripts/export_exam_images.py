#!/usr/bin/env python3
"""Materialize question images and link them from generated Markdown files.

New curated imports use data URIs, while a few legacy rows contain bare base64.
Support both forms and infer the legacy image type from decoded bytes.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"
DEFAULT_OUT = REPO_ROOT / "Project_Mia/backend/data_export"

DATA_URI = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$", re.DOTALL)


def extension_for(mime: str) -> str:
    return {
        "image/svg+xml": ".svg",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(mime.lower(), ".bin")


def sniff_extension(raw: bytes) -> str | None:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if raw.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    head = raw[:512].lstrip()
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head):
        return ".svg"
    return None


def decode_image(encoded: str) -> tuple[bytes, str] | None:
    text = encoded.strip()
    match = DATA_URI.match(text)
    if match:
        ext = extension_for(match.group("mime"))
        if ext == ".bin":
            return None
        try:
            return base64.b64decode(match.group("data")), ext
        except (binascii.Error, ValueError):
            return None

    # Legacy rows may contain bare base64 with whitespace and/or omitted padding.
    compact = "".join(text.split())
    if compact.lower().startswith("base64,"):
        compact = compact.split(",", 1)[1]
    compact += "=" * (-len(compact) % 4)
    try:
        raw = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        return None
    ext = sniff_extension(raw)
    if not ext:
        return None
    return raw, ext


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    out = args.out.resolve()
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    try:
        images = conn.execute(
            "SELECT q_id, paper_id, image_base64 FROM questions WHERE image_base64 IS NOT NULL AND image_base64 != ''"
        ).fetchall()
    finally:
        conn.close()

    linked = 0
    for q_id, paper_id, encoded in images:
        decoded = decode_image(encoded)
        if not decoded:
            print(f"Skipping unsupported image encoding for {q_id}")
            continue
        raw, ext = decoded

        dest = assets / f"{q_id}{ext}"
        dest.write_bytes(raw)

        paper_dir = out / "papers" / paper_id
        marker = f"q_id={q_id}"
        for md in paper_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            if marker not in text:
                continue
            placeholder = "> This question has an image in the SQLite source; base64 image data is intentionally omitted from the text export."
            image_ref = f"![Question image](../../assets/{dest.name})"
            if placeholder in text:
                text = text.replace(placeholder, image_ref, 1)
            elif image_ref not in text:
                text = text.replace(f"<!-- {marker}", f"{image_ref}\n\n<!-- {marker}", 1)
            md.write_text(text, encoding="utf-8")
            linked += 1
            break

    print(f"Exported and linked {linked} question images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
