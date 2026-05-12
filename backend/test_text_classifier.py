"""
test_text_classifier.py
Run from project root: python test_text_classifier.py
Runs detector first, then classifies each cropped section.
"""

from PIL import Image
from bmc_eval_scripts import detector, text_classifier

BMC_IMAGE_PATH = "test_images/bmc_sample.jpg"  # ← replace with your real BMC image


def test_classifier():
    print("TEST — Text Type Classifier...")
    image = Image.open(BMC_IMAGE_PATH).convert("RGB")

    sections = detector.detect(image)
    sections = text_classifier.classify_sections(sections)

    print(f"  {'Section':<30} {'Type'}")
    print(f"  {'-'*45}")
    for s in sections:
        print(f"  {s['name']:<30} {s['text_type']}")

    print("\n  ✅ Classification complete. Check types match your BMC (handwritten/printed).")


if __name__ == "__main__":
    test_classifier()