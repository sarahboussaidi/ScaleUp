from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a clean YOLO detection dataset for signatures.")
    parser.add_argument(
        "--source-root",
        default="data2/result_combine_new_data/result_combine_data",
        help="Path containing source test/images and test/labels.",
    )
    parser.add_argument(
        "--output-root",
        default="data2/signature_yolo_prepared",
        help="Output dataset root path.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split reproducibility.")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove output directory before creating new dataset.",
    )
    return parser.parse_args()


def _clamp(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def _polygon_to_bbox(vals: List[float]) -> Tuple[float, float, float, float] | None:
    if len(vals) < 6 or len(vals) % 2 != 0:
        return None

    xs = vals[0::2]
    ys = vals[1::2]

    if not xs or not ys:
        return None

    x_min = _clamp(min(xs))
    y_min = _clamp(min(ys))
    x_max = _clamp(max(xs))
    y_max = _clamp(max(ys))

    w = x_max - x_min
    h = y_max - y_min
    if w <= 0.0 or h <= 0.0:
        return None

    x_center = _clamp((x_min + x_max) / 2.0)
    y_center = _clamp((y_min + y_max) / 2.0)
    return x_center, y_center, w, h


def _clean_label_line(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None

    parts = s.split()

    try:
        class_id = int(float(parts[0]))
    except (ValueError, IndexError):
        return None

    if class_id != 0:
        # Single-class training for signatures.
        class_id = 0

    try:
        nums = [float(x) for x in parts[1:]]
    except ValueError:
        return None

    if len(nums) == 4:
        x, y, w, h = (_clamp(nums[0]), _clamp(nums[1]), _clamp(nums[2]), _clamp(nums[3]))
        if w <= 0.0 or h <= 0.0:
            return None
        return f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"

    bbox = _polygon_to_bbox(nums)
    if bbox is None:
        return None

    x, y, w, h = bbox
    return f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"


def _collect_pairs(images_dir: Path, labels_dir: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for img in sorted(images_dir.glob("*")):
        if not img.is_file():
            continue
        lbl = labels_dir / f"{img.stem}.txt"
        if lbl.exists():
            pairs.append((img, lbl))
    return pairs


def _ensure_dirs(root: Path) -> None:
    for split in ("train", "valid", "test"):
        (root / split / "images").mkdir(parents=True, exist_ok=True)
        (root / split / "labels").mkdir(parents=True, exist_ok=True)


def _write_yaml(root: Path) -> None:
    data = {
        "path": str(root.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": 1,
        "names": ["signature"],
    }
    with (root / "data.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def _split_counts(n: int, train_ratio: float, val_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    train_n = int(n * train_ratio)
    val_n = int(n * val_ratio)
    test_n = n - train_n - val_n
    return train_n, val_n, test_n


def main() -> None:
    args = parse_args()

    ratio_sum = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(ratio_sum - 1.0) > 1e-9:
        raise SystemExit("Split ratios must sum to 1.0")

    source_root = Path(args.source_root)
    output_root = Path(args.output_root)

    source_images = source_root / "test" / "images"
    source_labels = source_root / "test" / "labels"

    if not source_images.exists() or not source_labels.exists():
        raise SystemExit("Source dataset must contain test/images and test/labels")

    if output_root.exists() and args.force:
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    _ensure_dirs(output_root)

    pairs = _collect_pairs(source_images, source_labels)
    if not pairs:
        raise SystemExit("No matched image-label pairs found in source test split")

    random.seed(args.seed)
    random.shuffle(pairs)

    train_n, val_n, _ = _split_counts(len(pairs), args.train_ratio, args.val_ratio, args.test_ratio)
    split_map = {
        "train": pairs[:train_n],
        "valid": pairs[train_n : train_n + val_n],
        "test": pairs[train_n + val_n :],
    }

    total_bad_lines = 0
    total_empty_after_clean = 0
    written_images = 0
    written_labels = 0

    for split, items in split_map.items():
        img_out = output_root / split / "images"
        lbl_out = output_root / split / "labels"

        for img_path, lbl_path in items:
            cleaned_lines: list[str] = []
            for line in lbl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                cleaned = _clean_label_line(line)
                if cleaned is None:
                    if line.strip():
                        total_bad_lines += 1
                    continue
                cleaned_lines.append(cleaned)

            if not cleaned_lines:
                total_empty_after_clean += 1
                continue

            shutil.copy2(img_path, img_out / img_path.name)
            (lbl_out / f"{img_path.stem}.txt").write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
            written_images += 1
            written_labels += 1

    _write_yaml(output_root)

    print(f"Prepared dataset at: {output_root.resolve()}")
    print(f"Total source pairs: {len(pairs)}")
    print(f"Written image/label pairs: {written_images}/{written_labels}")
    print(f"Dropped malformed label lines: {total_bad_lines}")
    print(f"Dropped samples with no valid boxes: {total_empty_after_clean}")

    for split in ("train", "valid", "test"):
        img_count = len(list((output_root / split / "images").glob("*")))
        lbl_count = len(list((output_root / split / "labels").glob("*.txt")))
        print(f"{split}: images={img_count}, labels={lbl_count}")


if __name__ == "__main__":
    main()
