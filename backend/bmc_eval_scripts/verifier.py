"""
bmc/verifier.py
Step 1 — BMC Verifier
Loads bmc_verifier.pt (YOLOv8 classification model) and checks if an image is a BMC.
"""

import os
from pathlib import Path
from PIL import Image

MODEL_PATH = Path("bmc_eval_models/bmc_verifier.pt")


class BMCVerifier:
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

    def is_bmc(self, image: Image.Image) -> bool:
        """
        Returns True if the image is classified as a BMC, False otherwise.
        """
        self.load()
        results = self.model(image)
        # YOLOv8 classification: results[0].probs gives class probabilities
        probs = results[0].probs
        top_class = int(probs.top1)
        names = results[0].names  # {0: 'bmc', 1: 'not_bmc'} or similar
        label = names[top_class].lower()
        return "bmc" in label


# Module-level singleton
_verifier = BMCVerifier()


def verify(image: Image.Image) -> bool:
    """Returns True if image is a BMC, raises ValueError if not."""
    result = _verifier.is_bmc(image)
    if not result:
        raise ValueError("Uploaded image does not appear to be a Business Model Canvas.")
    return True