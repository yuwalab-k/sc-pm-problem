#!/usr/bin/env python3
"""
OCR a SC exam PDF pair (question + answer) using macOS Vision framework.

Usage:
  python3 scripts/ocr_pdf.py pdf/2024r06a_sc_pm_qs.pdf
  python3 scripts/ocr_pdf.py --all
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
PDF_DIR = ROOT / "pdf"
DATA_DIR = ROOT / "data" / "exams"


def parse_filename(stem: str) -> dict:
    """
    Examples:
      2024r06a_sc_pm_qs   -> year=2024, era='r06', period='秋', split=None
      2022r04h_sc_pm1_qs  -> year=2022, era='r04', period='春', split=1
      2019h31h_sc_pm1_qs  -> year=2019, era='h31', period='春', split=1
    """
    m = re.match(r"(\d{4})(h\d+|r\d+)(a|h|o)_sc_pm(\d?)_(qs|ans)", stem)
    if not m:
        raise ValueError(f"Cannot parse filename: {stem}")

    year = int(m.group(1))
    era_code = m.group(2)
    period_code = m.group(3)
    split_str = m.group(4)

    if era_code.startswith("h"):
        era_num = int(era_code[1:])
        era_label = f"平成{era_num}年度"
    else:
        era_num = int(era_code[1:])
        era_label = f"令和{era_num}年度" if era_num > 1 else "令和元年度"

    period_map = {"a": "秋", "h": "春", "o": "特別"}
    period = period_map[period_code]
    split = int(split_str) if split_str else None

    exam_label = "午後" if split is None else f"午後{'I' if split == 1 else 'II'}"

    return {
        "year": year,
        "era_label": era_label,
        "period": period,
        "split": split,
        "exam_label": exam_label,
        "label": f"{era_label}{period}試験 {exam_label}",
    }


IMAGE_PLACEHOLDER = "【 ここに図・表が入ります 】"
# Vertical gap threshold in normalized coords (0–1).
# ~4% of page height ≈ 2–3 lines at 200 dpi → treat as figure/table region.
GAP_THRESHOLD = 0.04


def ocr_image(image_path: str) -> str:
    import Vision
    from Foundation import NSURL

    url = NSURL.fileURLWithPath_(image_path)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLanguages_(["ja-JP", "en-US"])
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)

    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    success, error = handler.performRequests_error_([request], None)
    if not success:
        print(f"  Vision error: {error}", file=sys.stderr)
        return ""

    # Collect (top_y, text) sorted top-to-bottom.
    # Vision bbox: y=0 is bottom, y=1 is top → top of observation = y + height.
    observations = []
    for obs in request.results():
        candidates = obs.topCandidates_(1)
        if candidates:
            bbox = obs.boundingBox()
            top_y = bbox.origin.y + bbox.size.height
            observations.append((top_y, candidates[0].string()))

    if not observations:
        return ""

    observations.sort(key=lambda x: x[0], reverse=True)  # top → bottom

    lines = []
    prev_bottom = observations[0][0]  # bottom of first observation ≈ top_y (approx)

    for i, (top_y, text) in enumerate(observations):
        # bottom of this observation (approximate: top_y - one line height)
        # Use gap between prev observation's bottom and this observation's top
        if i > 0:
            prev_top, _ = observations[i - 1]
            _, prev_obs = observations[i - 1]
            # Re-fetch bottom via index isn't straightforward; use gap between tops
            # as a proxy: if gap between consecutive top_y values is large → image
            gap = observations[i - 1][0] - top_y
            if gap > GAP_THRESHOLD:
                lines.append(f"\n{IMAGE_PLACEHOLDER}\n")
        lines.append(text)

    return "\n".join(lines)


def ocr_pdf(pdf_path: Path, dpi: int = 200) -> list[str]:
    """Convert PDF to images and OCR each page. Returns list of page texts."""
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = os.path.join(tmpdir, "page")
        result = subprocess.run(
            ["pdftoppm", "-r", str(dpi), str(pdf_path), prefix],
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftoppm failed: {result.stderr.decode()}")

        ppm_files = sorted(Path(tmpdir).glob("page-*.ppm"))
        if not ppm_files:
            ppm_files = sorted(Path(tmpdir).glob("page*.ppm"))

        pages = []
        for i, ppm in enumerate(ppm_files, 1):
            print(f"  OCR page {i}/{len(ppm_files)}...", end="\r", flush=True)
            png_path = str(ppm).replace(".ppm", ".png")
            img = Image.open(str(ppm))
            img.save(png_path)
            text = ocr_image(png_path)
            pages.append(text)

        print(f"  OCR done: {len(pages)} pages      ")
        return pages


def find_pair(qs_path: Path) -> Path:
    ans_path = Path(str(qs_path).replace("_qs.pdf", "_ans.pdf"))
    if not ans_path.exists():
        raise FileNotFoundError(f"Answer PDF not found: {ans_path}")
    return ans_path


def process_pair(qs_path: Path) -> Path:
    stem = qs_path.stem  # e.g. "2024r06a_sc_pm_qs"
    exam_id = stem.replace("_qs", "")  # e.g. "2024r06a_sc_pm"
    out_path = DATA_DIR / f"{exam_id}.json"

    if out_path.exists():
        print(f"Skip (already exists): {out_path.name}")
        return out_path

    ans_path = find_pair(qs_path)
    meta = parse_filename(stem)

    print(f"\n[{meta['label']}] {qs_path.name}")
    print(f"  OCR question PDF ({qs_path.name})...")
    qs_pages = ocr_pdf(qs_path)

    print(f"  OCR answer PDF ({ans_path.name})...")
    ans_pages = ocr_pdf(ans_path)

    data = {
        "id": exam_id,
        "year": meta["year"],
        "era_label": meta["era_label"],
        "period": meta["period"],
        "split": meta["split"],
        "exam_label": meta["exam_label"],
        "label": meta["label"],
        "ocr_at": date.today().isoformat(),
        "question_pages": qs_pages,
        "answer_pages": ans_pages,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Saved: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", help="Path to _qs.pdf file")
    parser.add_argument("--all", action="store_true", help="Process all PDF pairs")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON")
    args = parser.parse_args()

    if args.all:
        qs_files = sorted(PDF_DIR.glob("*_qs.pdf"))
        print(f"Found {len(qs_files)} question PDFs")
        for qs in qs_files:
            if args.force:
                out = DATA_DIR / (qs.stem.replace("_qs", "") + ".json")
                out.unlink(missing_ok=True)
            process_pair(qs)
    elif args.pdf:
        qs_path = Path(args.pdf)
        if args.force:
            out = DATA_DIR / (qs_path.stem.replace("_qs", "") + ".json")
            out.unlink(missing_ok=True)
        process_pair(qs_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
