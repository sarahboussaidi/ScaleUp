from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 for signature object detection.")
    parser.add_argument("--data", default="data2/signature_yolo_prepared/data.yaml", help="Path to YOLO data.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model checkpoint")
    parser.add_argument(
        "--freeze",
        type=int,
        default=10,
        help=(
            "Number of initial layers to freeze for transfer learning. "
            "Set 0 to train all layers."
        ),
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--lr0", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--lrf", type=float, default=1e-2, help="Final LR multiplier")
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--optimizer", default="AdamW", choices=["SGD", "Adam", "AdamW", "auto"])
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", default=None, help="Device string (cpu, 0, 0,1, mps)")
    parser.add_argument("--project", default="runs/detect")
    parser.add_argument("--name", default="signature_yolo_clean")
    parser.add_argument("--exist-ok", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint in run dir")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and exit without training")
    return parser.parse_args()


def _device_arg(device: Optional[str]) -> Optional[str | int]:
    if device is None:
        return None
    value = str(device).strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    return value


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)

    if not data_path.exists():
        raise SystemExit(f"Data config not found: {data_path}")

    if args.dry_run:
        print("Dry run passed.")
        print(f"Data config: {data_path.resolve()}")
        print(f"Model: {args.model}")
        print(f"Freeze layers: {args.freeze}")
        print(f"Optimizer: {args.optimizer}, lr0={args.lr0}, lrf={args.lrf}, wd={args.weight_decay}")
        print(f"Epochs: {args.epochs}, imgsz: {args.imgsz}, batch: {args.batch}")
        return

    model = YOLO(args.model)
    train_kwargs = {
        "data": str(data_path),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "freeze": args.freeze,
        "lr0": args.lr0,
        "lrf": args.lrf,
        "weight_decay": args.weight_decay,
        "optimizer": args.optimizer,
        "patience": args.patience,
        "workers": args.workers,
        "project": args.project,
        "name": args.name,
        "exist_ok": args.exist_ok,
        "resume": args.resume,
    }
    device = _device_arg(args.device)
    if device is not None:
        train_kwargs["device"] = device

    print("Starting YOLO fine-tuning with transfer-learning settings:")
    print({k: v for k, v in train_kwargs.items() if k != "data"})

    model.train(
        data=str(data_path),
        **{k: v for k, v in train_kwargs.items() if k != "data"},
    )

    metrics = model.val(data=str(data_path))
    print(metrics)

    run_weights_dir = Path(args.project) / args.name / "weights"
    best = run_weights_dir / "best.pt"
    last = run_weights_dir / "last.pt"
    if best.exists():
        print(f"Best model: {best.resolve()}")
    if last.exists():
        print(f"Last model: {last.resolve()}")


if __name__ == "__main__":
    main()
