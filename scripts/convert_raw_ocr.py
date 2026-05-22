#!/usr/bin/env python3
"""
Convert _raw_ocr fields in table items to headers + rows structure.
Results are approximate; manual verification required.
"""
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "exams"


def parse_raw_ocr(raw: str) -> dict:
    """
    Convert raw OCR text to a best-effort table structure.
    - title: extracted "表N ..." heading
    - headers: [] (left empty; too ambiguous to split automatically)
    - rows: each \n-separated line as [line_text]
    - _raw_ocr: preserved as-is
    """
    # Extract title: 表N + up to first \n, or up to 30 chars if no \n
    title = ""
    body = raw

    title_m = re.match(r'^(表\d+(?:\s*の\d+)?(?:\s+[^\n]{0,60})?)', raw)
    if title_m:
        # Split on first \n if present; otherwise title is just 表N word
        newline_pos = raw.find("\n")
        if newline_pos != -1:
            title = raw[:newline_pos].strip()
            body = raw[newline_pos + 1:].strip()
        else:
            # No newline: title is just 表N, body is everything after
            bare = re.match(r'^(表\d+(?:\s*の\d+)?)\s*', raw)
            if bare:
                title = bare.group(1)
                body = raw[bare.end():].strip()
            else:
                title = ""
                body = raw

    # Split body by \n; each non-empty line becomes one row (single cell)
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    rows = [[line] for line in lines]

    # If body had no \n and body is non-empty, put it as one row
    if not rows and body:
        rows = [[body]]

    return {
        "title": title,
        "headers": [],
        "rows": rows,
    }


def process_file(path: Path) -> bool:
    """Process a single JSON file. Returns True if modified."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  SKIP (invalid JSON): {path}: {e}", file=sys.stderr)
        return False

    modified = False
    for prob in data.get("problems", []):
        for item in prob.get("items", []):
            if item.get("type") == "table" and "_raw_ocr" in item:
                raw = item["_raw_ocr"]
                parsed = parse_raw_ocr(raw)

                item["title"] = parsed["title"]
                item["headers"] = parsed["headers"]
                item["rows"] = parsed["rows"]
                modified = True

    if modified:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return modified


def main():
    files = sorted(DATA_DIR.glob("*/*.json"))
    total = 0
    changed = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        has_raw = any(
            item.get("type") == "table" and "_raw_ocr" in item
            for prob in data.get("problems", [])
            for item in prob.get("items", [])
        )
        if not has_raw:
            continue
        total += 1
        if process_file(f):
            changed += 1
            print(f"  converted: {f}")

    print(f"\nDone: {changed}/{total} files updated.")


if __name__ == "__main__":
    main()
