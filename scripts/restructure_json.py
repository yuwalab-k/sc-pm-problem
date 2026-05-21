#!/usr/bin/env python3
"""
Migrate existing flat-page JSON to block-structured JSON.

Old schema:
  question_pages: [str, ...]      # flat list of page texts
  answer_pages:   [str, ...]

New schema:
  pages:          [{page, is_content, blocks: [{type,content}|{type,src,caption}]}]
  answer_pages:   [{page, is_content, blocks: [...]}]

Usage:
  python3 scripts/restructure_json.py          # migrate all
  python3 scripts/restructure_json.py data/exams/2024r06a_sc_pm.json
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "exams"

IMAGE_PLACEHOLDER = "【 ここに図・表が入ります 】"

# Patterns that indicate exam instructions rather than problem content
_NOISE_PATTERNS = [
    "注意事項",
    "試験開始の合図",
    "退室可能時間",
    "答案用紙",
    "受験番号",
    "監督員",
    "黒鉛筆",
    "シャープペンシル",
]


def is_content_page(text: str, page_num: int, total: int) -> bool:
    """Return False for cover / instruction pages."""
    # Only check near the edges of the document
    if page_num > 3 and page_num < total - 1:
        return True
    noise_hits = sum(1 for p in _NOISE_PATTERNS if p in text)
    return noise_hits < 2


def split_into_blocks(text: str) -> list[dict]:
    """
    Split page text on IMAGE_PLACEHOLDER markers.
    Returns a list of block dicts:
      {"type": "text",  "content": "..."}
      {"type": "image", "src": null, "caption": ""}
    """
    parts = re.split(re.escape(IMAGE_PLACEHOLDER), text)
    blocks = []
    for i, part in enumerate(parts):
        cleaned = part.strip()
        if cleaned:
            blocks.append({"type": "text", "content": cleaned})
        # Between each pair of parts there was a placeholder
        if i < len(parts) - 1:
            blocks.append({"type": "image", "src": None, "caption": ""})
    return blocks


def structurize_pages(raw_pages: list[str]) -> list[dict]:
    total = len(raw_pages)
    result = []
    for i, text in enumerate(raw_pages, 1):
        result.append({
            "page": i,
            "is_content": is_content_page(text, i, total),
            "blocks": split_into_blocks(text),
        })
    return result


def migrate_file(path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Already migrated
    if "pages" in data and isinstance(data["pages"][0], dict) and "blocks" in data["pages"][0]:
        print(f"  Skip (already migrated): {path.name}")
        return

    qs_raw = data.pop("question_pages", [])
    ans_raw = data.pop("answer_pages", [])

    data["pages"] = structurize_pages(qs_raw)
    data["answer_pages"] = structurize_pages(ans_raw)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    content_count = sum(1 for p in data["pages"] if p["is_content"])
    image_count = sum(
        1 for p in data["pages"]
        for b in p["blocks"] if b["type"] == "image"
    )
    print(f"  {path.name}: {len(data['pages'])}p ({content_count} content), {image_count} image slots")


def main():
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        paths = sorted(DATA_DIR.glob("*.json"))

    print(f"Migrating {len(paths)} files...")
    for p in paths:
        migrate_file(p)
    print("Done.")


if __name__ == "__main__":
    main()
