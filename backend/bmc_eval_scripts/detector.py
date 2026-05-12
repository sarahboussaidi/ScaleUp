"""
bmc/detector.py
Step 2 — BMC Detector
Loads bmc_detector.pt (YOLOv8 detection model) and crops all 9 BMC sections.
"""

from pathlib import Path
from PIL import Image

MODEL_PATH = Path("bmc_eval_models/bmc_detector.pt")

BMC_SECTIONS = [
    "key-partners",
    "key-activities",
    "key-resources",
    "value-propositions",
    "customer-relationships",
    "channels",
    "customer-segments",
    "cost-structure",
    "revenue-streams",
]

# Friendly display names aligned with JSON contract
SECTION_NAMES = {
    "key-partners": "Key Partners",
    "key-activities": "Key Activities",
    "key-resources": "Key Resources",
    "value-propositions": "Value Propositions",
    "customer-relationships": "Customer Relationships",
    "channels": "Channels",
    "customer-segments": "Customer Segments",
    "cost-structure": "Cost Structure",
    "revenue-streams": "Revenue Streams",
}


class BMCDetector:
    def __init__(self):
        self.model = None

    def load(self):
        if self.model is not None:
            return
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError("ultralytics is required: pip install ultralytics")
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        self.model = YOLO(str(MODEL_PATH))

    def detect(self, image: Image.Image) -> list[dict]:
        """
        Detects and crops the 9 BMC sections.
        Returns a list of dicts:
          [{"id": str, "name": str, "crop": PIL.Image}, ...]
        Raises ValueError if fewer than 9 sections are found.
        """
        self.load()
        results = self.model(image)
        boxes = results[0].boxes
        names = results[0].names  # {int: label_str}

        sections = []
        for box in boxes:
            cls_id = int(box.cls[0])
            label = names[cls_id].lower().replace("_", "-").replace(" ", "-")
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            crop = image.crop((x1, y1, x2, y2))
            section_id = label if label in SECTION_NAMES else label
            sections.append({
                "id": section_id,
                "name": SECTION_NAMES.get(section_id, label.replace("-", " ").title()),
                "crop": crop,
            })

        if len(sections) < 9:
            raise ValueError(
                f"Only {len(sections)} BMC sections detected; expected 9. "
                "Ensure the image is clear and all sections are visible."
            )

        return sections


# Module-level singleton
_detector = BMCDetector()


def detect(image: Image.Image) -> list[dict]:
    """Detect and return cropped BMC sections."""
    return _detector.detect(image)