import os
import re
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image


try:
    import easyocr
except Exception:
    easyocr = None


EASYOCR_READER = None


def get_easyocr_reader():
    global EASYOCR_READER

    if easyocr is None:
        return None

    if EASYOCR_READER is None:
        EASYOCR_READER = easyocr.Reader(["en"], gpu=False)

    return EASYOCR_READER


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_with_pymupdf(pdf_path: str):
    """
    Extract embedded text from PDF pages.
    Works well for digital PDFs.
    """
    pages = []

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        page_text = page.get_text("text") or ""

        pages.append({
            "page_number": page_index + 1,
            "method": "pymupdf_text",
            "text": clean_text(page_text),
            "char_count": len(page_text.strip())
        })

    doc.close()
    return pages


def render_pdf_page_to_image(pdf_path: str, page_index: int, zoom: float = 2.0):
    """
    Render a PDF page to image for OCR fallback.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()

    return image


def easyocr_image_to_text(image: Image.Image):
    """
    Run EasyOCR on PIL image.
    """
    reader = get_easyocr_reader()

    if reader is None:
        return ""

    image_np = np.array(image)
    results = reader.readtext(image_np, detail=0, paragraph=True)

    if not results:
        return ""

    return clean_text("\n".join(results))


def extract_text_from_pdf_with_ocr(pdf_path: str, min_chars_per_page: int = 80):
    """
    Hybrid extraction:
    1. Try PyMuPDF text extraction.
    2. If a page has very little text, render it and apply EasyOCR.
    """
    pages = extract_text_with_pymupdf(pdf_path)
    final_pages = []

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"]

        if len(page_text.strip()) >= min_chars_per_page:
            final_pages.append(page)
            continue

        try:
            image = render_pdf_page_to_image(pdf_path, page_number - 1)
            ocr_text = easyocr_image_to_text(image)

            final_pages.append({
                "page_number": page_number,
                "method": "easyocr_fallback",
                "text": clean_text(ocr_text),
                "char_count": len(ocr_text.strip())
            })

        except Exception as e:
            final_pages.append({
                "page_number": page_number,
                "method": "ocr_failed",
                "text": page_text,
                "char_count": len(page_text.strip()),
                "error": str(e)
            })

    return final_pages


def extract_text_from_image(image_path: str):
    image = Image.open(image_path).convert("RGB")
    return easyocr_image_to_text(image)


def extract_text_from_file(file_path: str):
    """
    Main entry point used by Flask.
    Supports PDF, TXT, MD, and images.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        pages = extract_text_from_pdf_with_ocr(file_path)
        full_text = "\n\n".join(
            [f"\n--- Page {p['page_number']} ({p['method']}) ---\n{p['text']}" for p in pages]
        )
        return clean_text(full_text)

    if ext in [".txt", ".md"]:
        return clean_text(Path(file_path).read_text(encoding="utf-8", errors="ignore"))

    if ext in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"]:
        return clean_text(extract_text_from_image(file_path))

    return ""


def split_candidate_requirements(text: str):
    """
    Extract candidate requirement sentences from uploaded/generated SRS.
    """
    if not text:
        return []

    lines = re.split(r"[\n\r]+", text)
    candidates = []

    requirement_patterns = [
        r"\bshall\b",
        r"\bmust\b",
        r"\bshould\b",
        r"\bwill\b",
        r"\brequired to\b",
        r"\bthe system\b",
        r"\busers? can\b",
        r"\busers? shall\b",
        r"\busers? must\b",
    ]

    for line in lines:
        clean = line.strip(" -•\t")
        if len(clean) < 20:
            continue

        lower = clean.lower()

        if any(re.search(pattern, lower) for pattern in requirement_patterns):
            candidates.append(clean)

    # fallback sentence split if no line-based candidates
    if len(candidates) < 3:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            clean = sentence.strip()
            lower = clean.lower()

            if len(clean) >= 20 and any(re.search(pattern, lower) for pattern in requirement_patterns):
                candidates.append(clean)

    # remove duplicates
    seen = set()
    unique = []

    for req in candidates:
        key = re.sub(r"\s+", " ", req.lower())
        if key not in seen:
            seen.add(key)
            unique.append(req)

    return unique

def detect_srs_sections(text: str):
    """
    Detect standard SRS sections from extracted text.
    Used by evaluator.py to compute section coverage.
    """
    if not text:
        return []

    text_lower = text.lower()

    section_patterns = {
        "Introduction": [
            r"\bintroduction\b",
            r"\bpurpose\b",
            r"\bscope\b",
        ],
        "General Description": [
            r"\bgeneral description\b",
            r"\boverall description\b",
            r"\bproduct perspective\b",
            r"\bproduct functions\b",
            r"\buser characteristics\b",
        ],
        "Functional Requirements": [
            r"\bfunctional requirements\b",
            r"\bfunctional requirement\b",
            r"\bfr[-\s]?\d+",
        ],
        "Non-Functional Requirements": [
            r"\bnon[-\s]?functional requirements\b",
            r"\bnon functional requirements\b",
            r"\bnfr[-\s]?\d+",
            r"\bquality requirements\b",
        ],
        "Interface Requirements": [
            r"\binterface requirements\b",
            r"\bexternal interface\b",
            r"\buser interface\b",
            r"\bapi\b",
        ],
        "Performance Requirements": [
            r"\bperformance requirements\b",
            r"\bperformance\b",
            r"\bresponse time\b",
            r"\blatency\b",
            r"\bthroughput\b",
        ],
        "Security Requirements": [
            r"\bsecurity requirements\b",
            r"\bsecurity\b",
            r"\bauthentication\b",
            r"\bauthorization\b",
            r"\bprivacy\b",
            r"\baccess control\b",
        ],
        "Acceptance Criteria": [
            r"\bacceptance criteria\b",
            r"\bacceptance test\b",
            r"\bvalidation criteria\b",
        ],
        "Risks and Assumptions": [
            r"\brisks and assumptions\b",
            r"\brisks\b",
            r"\bassumptions\b",
            r"\bconstraints\b",
        ],
        "Conclusion": [
            r"\bconclusion\b",
            r"\bsummary\b",
        ],
    }

    found_sections = []

    for section_name, patterns in section_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found_sections.append(section_name)
                break

    return found_sections