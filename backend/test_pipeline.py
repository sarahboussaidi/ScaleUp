"""
test_pipeline.py
Run from project root: python test_pipeline.py
Full end-to-end test: image → JSON result.
"""

import json
from PIL import Image
import bmc_eval_scripts as bmc

BMC_IMAGE_PATH = "test_images/bmc_sample.jpg"  # ← replace with your real BMC image


def test_pipeline():
    print("TEST — Full Pipeline (Verifier → Detector → Classifier → LLaMA)...")
    print("  ⏳ This will take a while on first run (models loading).\n")

    image = Image.open(BMC_IMAGE_PATH).convert("RGB")

    try:
        result = bmc.run(image)

        print(f"  ✅ Pipeline completed\n")
        print(f"  Overall Score : {result['overallScore']}")
        print(f"  Sections      : {len(result['boxes'])}")
        print(f"  Strengths     : {result['strengths']}")
        print(f"  Weaknesses    : {result['weaknesses']}")
        print(f"  Coherence     : {result['coherence']['score']}")
        print()

        # Save full result for inspection
        with open("test_output/pipeline_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("  📄 Full result saved to test_output/pipeline_result.json")

    except ValueError as e:
        print(f"  ❌ Pipeline rejected input — {e}")
    except Exception as e:
        print(f"  ❌ Pipeline error — {e}")


if __name__ == "__main__":
    import os
    os.makedirs("test_output", exist_ok=True)
    test_pipeline()