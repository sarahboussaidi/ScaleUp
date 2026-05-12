"""
bmc/pipeline.py
Master orchestrator — wires all 4 steps together.
Verifier → Detector → Classifier → LLaMA Pipeline
"""

from PIL import Image
from bmc_eval_scripts import verifier, detector, text_classifier, llama_pipeline


def run(image: Image.Image) -> dict:
    """
    Full BMC analysis pipeline.
    Args:
        image: PIL Image of the uploaded BMC.
    Returns:
        JSON-contract-compliant dict ready to send to the frontend.
    Raises:
        ValueError: if the image is not a BMC or fewer than 9 sections are detected.
    """
    # Step 1 — Verify
    verifier.verify(image)

    # Step 2 — Detect & crop 9 sections
    sections = detector.detect(image)

    # Step 3 — Classify text type per section
    sections = text_classifier.classify_sections(sections)

    # Step 4 — OCR + RAG + LLaMA evaluation
    result = llama_pipeline.run(sections)

    return result