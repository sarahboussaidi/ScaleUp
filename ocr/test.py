import argparse
import json
from pathlib import Path

from ocr.document_analyzer import DocumentAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OCR analysis on a document image")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument(
        "--annotated",
        default="generated/ocr_annotated.png",
        help="Path to save annotated output image",
    )
    args = parser.parse_args()

    analyzer = DocumentAnalyzer()
    result = analyzer.analyze(args.image, save_annotated_to=args.annotated)

    print("\n===== OCR TEXT (first 1200 chars) =====\n")
    print(result["text"][:1200])
    print("\n===== SUMMARY =====\n")
    print(json.dumps({
        "entities": result["entities"][:20],
        "ocr_items": len(result["ocr_results"]),
        "keyword_hits": result["keyword_hits"][:20],
        "annotated_image_path": result.get("annotated_image_path"),
    }, indent=2))


if __name__ == "__main__":
    main()