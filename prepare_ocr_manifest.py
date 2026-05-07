from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create OCR JSONL manifests from image/text pairs for TrOCR fine-tuning."
    )
    parser.add_argument("--images-dir", required=True, help="Directory containing source images")
    parser.add_argument(
        "--labels-dir",
        default=None,
        help="Directory containing .txt labels with same stem as image. Defaults to images dir.",
    )
    parser.add_argument("--train-out", default="data/ocr_train.jsonl")
    parser.add_argument("--valid-out", default="data/ocr_valid.jsonl")
    parser.add_argument(
        "--funsd-root",
        default=None,
        help="Optional FUNSD root; if set, build rows from annotations/images folders",
    )
    parser.add_argument("--max-funsd-rows", type=int, default=5000)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-chars", type=int, default=2)
    return parser.parse_args()


def _collect_pairs(images_dir: Path, labels_dir: Path, min_chars: int) -> List[Tuple[Path, str]]:
    rows: List[Tuple[Path, str]] = []
    for image_path in sorted(images_dir.glob("*")):
        if image_path.suffix.lower() not in IMAGE_EXTS or not image_path.is_file():
            continue
        label_path = labels_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue

        text = label_path.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) < min_chars:
            continue
        rows.append((image_path.resolve(), text))
    return rows


def _write_jsonl(path: Path, rows: List[Tuple[Path, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for image_path, text in rows:
            obj = {"image_path": str(image_path), "text": text}
            f.write(json.dumps(obj, ensure_ascii=True) + "\n")


def _collect_funsd_pairs(funsd_root: Path, min_chars: int, max_rows: int) -> List[Tuple[Path, str]]:
    rows: List[Tuple[Path, str]] = []
    splits = [funsd_root / "training_data", funsd_root / "testing_data"]
    for split in splits:
        ann_dir = split / "annotations"
        img_dir = split / "images"
        if not ann_dir.exists() or not img_dir.exists():
            continue

        for ann_path in sorted(ann_dir.glob("*.json")):
            try:
                doc = json.loads(ann_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            form = doc.get("form", [])
            words: List[str] = []
            for item in form:
                text = str(item.get("text", "")).strip()
                if text:
                    words.append(text)
            merged_text = " ".join(words).strip()
            if len(merged_text) < min_chars:
                continue

            image_path = img_dir / f"{ann_path.stem}.png"
            if not image_path.exists():
                continue
            rows.append((image_path.resolve(), merged_text))
            if len(rows) >= max_rows:
                return rows
    return rows


def main() -> None:
    args = parse_args()
    images_dir = Path(args.images_dir)
    labels_dir = Path(args.labels_dir) if args.labels_dir else images_dir

    if not images_dir.exists():
        raise SystemExit(f"Images dir not found: {images_dir}")
    if not labels_dir.exists():
        raise SystemExit(f"Labels dir not found: {labels_dir}")

    rows = _collect_pairs(images_dir, labels_dir, min_chars=args.min_chars)
    if len(rows) < 2 and args.funsd_root:
        rows = _collect_funsd_pairs(Path(args.funsd_root), min_chars=args.min_chars, max_rows=args.max_funsd_rows)
    if len(rows) < 2:
        raise SystemExit("Not enough OCR pairs found from labels or FUNSD fallback. Need at least 2 samples.")

    import random

    random.seed(args.seed)
    random.shuffle(rows)

    valid_ratio = max(0.0, min(0.9, float(args.valid_ratio)))
    valid_count = max(1, int(len(rows) * valid_ratio))
    valid_rows = rows[:valid_count]
    train_rows = rows[valid_count:]
    if not train_rows:
        train_rows = valid_rows
        valid_rows = []

    train_out = Path(args.train_out)
    valid_out = Path(args.valid_out)
    _write_jsonl(train_out, train_rows)
    if valid_rows:
        _write_jsonl(valid_out, valid_rows)

    print(f"Train rows: {len(train_rows)} -> {train_out.resolve()}")
    if valid_rows:
        print(f"Valid rows: {len(valid_rows)} -> {valid_out.resolve()}")
    else:
        print("No validation rows written (dataset too small).")


if __name__ == "__main__":
    main()
