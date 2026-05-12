"""
test_verifier.py
Run from project root: python test_verifier.py
Requires: a real BMC image and any random non-BMC image.
"""

from PIL import Image
from bmc_eval_scripts import verifier

BMC_IMAGE_PATH = "test_images/bmc_sample.jpg"       # ← replace with your real BMC image
RANDOM_IMAGE_PATH = "test_images/random_sample.jpg" # ← replace with any non-BMC image


def test_valid_bmc():
    print("TEST 1 — Valid BMC image...")
    image = Image.open(BMC_IMAGE_PATH).convert("RGB")
    try:
        verifier.verify(image)
        print("  ✅ PASSED — image accepted as BMC\n")
    except ValueError as e:
        print(f"  ❌ FAILED — {e}\n")


def test_invalid_image():
    print("TEST 2 — Non-BMC image (should be rejected)...")
    image = Image.open(RANDOM_IMAGE_PATH).convert("RGB")
    try:
        verifier.verify(image)
        print("  ❌ FAILED — image should have been rejected\n")
    except ValueError as e:
        print(f"  ✅ PASSED — correctly rejected: {e}\n")


if __name__ == "__main__":
    test_valid_bmc()
    test_invalid_image()