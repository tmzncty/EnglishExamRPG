#!/usr/bin/env python3
"""Materialize question images and link them from generated Markdown files."""

from __future__ import annotations

import argparse
import base64
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
    }.get(mime.lower(), ".bin")


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
        match = DATA_URI.match(encoded.strip())
        if not match:
            print(f"Skipping unsupported image encoding for {q_id}")
            continue
        mime = match.group("mime")
        ext = extension_for(mime)
        if ext == ".bin":
            print(f"Skipping unsupported image MIME {mime!r} for {q_id}")
            continue

        dest = assets / f"{q_id}{ext}"
        dest.write_bytes(base64.b64decode(match.group("data")))

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
