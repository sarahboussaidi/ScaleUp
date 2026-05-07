from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
except ImportError as exc:  # pragma: no cover - handled at runtime
    YOLO = None  # type: ignore[assignment]
    _YOLO_IMPORT_ERROR = exc
else:
    _YOLO_IMPORT_ERROR = None


MODEL_CANDIDATES = [
    Path("runs/detect/runs/detect/signature_yolo_clean/weights/best.pt"),
    Path("runs/detect/signature_yolo_clean/weights/best.pt"),
    Path("runs/detect/signature_yolo_results/yolov8_signature/weights/best.pt"),
    Path("data2/chekpoint_last.pt"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLO signature detection on a local image.")
    parser.add_argument("image", type=Path, help="Path to the image file to analyze")
    parser.add_argument("--model", type=Path, default=None, help="Optional explicit YOLO .pt checkpoint")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="IoU threshold")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to save the annotated image. Defaults to generated/signature_detect_<timestamp>.png",
    )
    return parser.parse_args()


def load_model(explicit_model: Optional[Path] = None) -> Tuple[Any, Path]:
    if YOLO is None:
        raise RuntimeError(
            "Ultralytics is not installed. Install requirements first."
        ) from _YOLO_IMPORT_ERROR

    candidates = [explicit_model] if explicit_model is not None else []
    candidates.extend(MODEL_CANDIDATES)

    for model_path in candidates:
        if model_path is None:
            continue
        if model_path.exists():
            return YOLO(str(model_path)), model_path

    raise FileNotFoundError(
        "No YOLO signature detector found. Provide --model or train one of the expected checkpoints."
    )


def run_detection(image_path: Path, model: Any, conf: float, iou: float) -> Dict[str, Any]:
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image)

    results = model.predict(source=image_np, conf=conf, iou=iou, verbose=False)
    if not results:
        return {"count": 0, "detections": [], "annotated_image": None}

    result = results[0]
    detections: List[Dict[str, Any]] = []
    names = result.names or {}

    if result.boxes is not None and len(result.boxes) > 0:
        xyxy_list = result.boxes.xyxy.cpu().tolist()
        conf_list = result.boxes.conf.cpu().tolist()
        cls_list = result.boxes.cls.cpu().tolist()

        for xyxy, score, cls_idx in zip(xyxy_list, conf_list, cls_list):
            idx = int(cls_idx)
            detections.append(
                {
                    "class_id": idx,
                    "class_name": str(names.get(idx, idx)),
                    "confidence": round(float(score), 4),
                    "box_xyxy": [round(float(v), 2) for v in xyxy],
                }
            )

    plotted_bgr = result.plot()
    plotted_rgb = plotted_bgr[:, :, ::-1]
    annotated_image = Image.fromarray(plotted_rgb)

    return {
        "count": len(detections),
        "detections": detections,
        "annotated_image": annotated_image,
    }


def predict_signature(
    image_path: str | Path,
    model_path: str | Path | None = None,
    conf: float = 0.25,
    iou: float = 0.45,
    output_path: str | Path | None = None,
) -> Dict[str, Any]:
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image not found: {image_file}")

    explicit_model = Path(model_path) if model_path is not None else None
    model, resolved_model_path = load_model(explicit_model)
    result = run_detection(image_file, model, conf, iou)

    resolved_output_path = Path(output_path) if output_path is not None else None
    if resolved_output_path is None:
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        resolved_output_path = Path("generated") / f"signature_detect_{stamp}.png"

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    if result["annotated_image"] is not None:
        result["annotated_image"].save(resolved_output_path)

    return {
        "model": resolved_model_path.name,
        "image": str(image_file),
        "count": result["count"],
        "detections": result["detections"],
        "annotated_image": str(resolved_output_path) if result["annotated_image"] is not None else None,
    }


def main() -> int:
    args = parse_args()
    payload = predict_signature(args.image, args.model, args.conf, args.iou, args.output)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())