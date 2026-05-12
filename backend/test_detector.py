"""
test_detector.py
Run from project root: python test_detector.py
Saves cropped section images to test_output/ so you can visually verify them.
"""

import os
from PIL import Image
from bmc_eval_scripts import detector

BMC_IMAGE_PATH = "test_images/bmc_sample.jpg"  # ← replace with your real BMC image
OUTPUT_DIR = "test_output/crops"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_detector():
    print("TEST — BMC Detector...")
    image = Image.open(BMC_IMAGE_PATH).convert("RGB")

    try:
        sections = detector.detect(image)
        print(f"  ✅ Detected {len(sections)} sections (expected 9)\n")

        for s in sections:
            out_path = os.path.join(OUTPUT_DIR, f"{s['id']}.jpg")
            s["crop"].save(out_path)
            print(f"  📦 {s['name']:30s} → saved to {out_path}")

        print(f"\n  Open test_output/crops/ to visually verify all 9 crops.")

    except ValueError as e:
        print(f"  ❌ FAILED — {e}")


if __name__ == "__main__":
    test_detector()