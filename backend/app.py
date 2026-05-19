"""
Pitch Analyzer API - Backend Service
Simplified for Next.js integration
"""

from flask import Flask, request, jsonify
from flask import send_file, send_from_directory
from flask_cors import CORS
import cv2
import re
import numpy as np
import json
import os
import base64
import re
import shutil
import subprocess
import tensorflow as tf
import traceback
import importlib
import importlib.util
import joblib
import mediapipe as mp
import librosa
import io
import tempfile
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from werkzeug.utils import secure_filename

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from Bmc_generation.document_classifier_routes import doc_classifier_bp, init_document_classifier
except Exception as exc:
    print(f"[WARN] Document classifier routes unavailable: {exc}")
    doc_classifier_bp = None

    def init_document_classifier():
        return None


try:
    from Bmc_generation.bmc_processor_routes import bmc_processor_bp, init_bmc_processor
except Exception as exc:
    print(f"[WARN] BMC processor routes unavailable: {exc}")
    bmc_processor_bp = None

    def init_bmc_processor():
        return None

try:
    from bmc_eval_routes import bmc_eval_bp, init_bmc_eval
except Exception as exc:
    print(f"[WARN] BMC eval routes unavailable: {exc}")
    bmc_eval_bp = None
    def init_bmc_eval():
        return None

from strength_predictor import detect_bad_words, hybrid_strength_predict
from SRS.srs_engine.document_parser import extract_text_from_file
from SRS.srs_engine.generator import generate_srs_document
from SRS.srs_engine.xai import get_generation_xai_summary
from SRS.srs_engine.model_based_evaluator import evaluate_srs_with_models, save_evaluation_report
try:
    from speech_strength_app import transcribe_audio
except Exception:
    transcribe_audio = None

try:
    from legal_document_intelligence import LegalDocumentIntelligence
    from intelligent_nda_filler import IntelligentNDAFiller
    from template_generator import TemplateDocumentGenerator
    LEGAL_FEATURES_AVAILABLE = True
except Exception as exc:
    print(f"[WARN] Legal feature modules unavailable: {exc}")
    LegalDocumentIntelligence = None
    IntelligentNDAFiller = None
    TemplateDocumentGenerator = None
    LEGAL_FEATURES_AVAILABLE = False

load_model = tf.keras.models.load_model

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Register document classifier blueprint
if doc_classifier_bp is not None:
    app.register_blueprint(doc_classifier_bp, url_prefix='/api')

# Register BMC processor blueprint
if bmc_processor_bp is not None:
    app.register_blueprint(bmc_processor_bp, url_prefix='/api')

# Register bmc eval
if bmc_eval_bp is not None:
    app.register_blueprint(bmc_eval_bp, url_prefix='/api')

# Get the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
VOICE_EMOTION_MODEL_PATH = os.path.join(MODELS_DIR, "best_cnn2d_v2.keras")
_MARKETING_DIR_CANDIDATES = [
    Path(MODELS_DIR) / "marketing" / "notebooks marketing",
    Path(MODELS_DIR) / "marketing models" / "notebooks marketing",
]
MARKETING_NOTEBOOK_DIR = next((candidate for candidate in _MARKETING_DIR_CANDIDATES if candidate.exists()), _MARKETING_DIR_CANDIDATES[0])
MARKETING_MODELS_DIR = MARKETING_NOTEBOOK_DIR.parent
MARKETING_OUTPUTS_DIR = os.path.join(MARKETING_NOTEBOOK_DIR, "outputs")

for search_path in (MARKETING_MODELS_DIR, MARKETING_NOTEBOOK_DIR):
    search_path_str = str(search_path)
    if search_path_str not in sys.path:
        sys.path.insert(0, search_path_str)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
OUTPUT_DIR = MARKETING_OUTPUTS_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# SRS uploaded document vision
# -----------------------------
SRS_PAGE_CLASSES = [
    "appendix_page",
    "content_page",
    "cover_page",
    "low_text_page",
    "toc_page",
]

SRS_RESNET_CACHE = {
    "loaded": False,
    "model": None,
    "transform": None,
    "classes": SRS_PAGE_CLASSES,
    "status": "not_loaded",
    "error": None,
}


def _humanize_page_type(label):
    label = str(label or "unknown_page").replace("_", " ").strip()
    return label[:1].upper() + label[1:]


def _heuristic_srs_page_type(text, filename=""):
    """Fallback only when the trained ResNet checkpoint cannot be loaded."""
    combined = f"{filename}\n{text or ''}".lower()

    if len(combined.strip()) < 40:
        return "low_text_page", 0.55, "Very little OCR/text was detected, so the page is considered low-text."

    if "table of contents" in combined or "contents" in combined or "toc" in combined:
        return "toc_page", 0.72, "OCR/text contains table-of-contents indicators."

    if "appendix" in combined or "annex" in combined:
        return "appendix_page", 0.70, "OCR/text contains appendix or annex indicators."

    cover_keywords = [
        "software requirements specification",
        "prepared by",
        "project title",
        "version",
        "author",
        "submitted",
    ]
    if any(keyword in combined for keyword in cover_keywords):
        return "cover_page", 0.68, "OCR/text contains cover-page metadata indicators."

    return "content_page", 0.62, "The page contains normal requirement/content text."


def _load_srs_resnet_classifier():
    """
    Load the trained ResNet18 page classifier when the checkpoint exists.
    If it cannot be loaded, the evaluator still returns a clear fallback status.
    """
    if SRS_RESNET_CACHE["loaded"]:
        return SRS_RESNET_CACHE

    model_path = os.path.join(
        BASE_DIR,
        "SRS",
        "srs_models",
        "cv",
        "v4_resnet18_page_classifier.pt",
    )

    if not os.path.exists(model_path):
        SRS_RESNET_CACHE.update({
            "loaded": True,
            "status": "model_not_found",
            "error": f"ResNet checkpoint not found at {model_path}",
        })
        return SRS_RESNET_CACHE

    try:
        import torch
        from torchvision import models, transforms

        checkpoint = torch.load(model_path, map_location="cpu")
        class_names = None
        state_dict = checkpoint

        if isinstance(checkpoint, dict):
            for key in ["class_names", "classes", "labels"]:
                if key in checkpoint and checkpoint[key]:
                    class_names = list(checkpoint[key])
                    break

            if class_names is None and "class_to_idx" in checkpoint:
                class_to_idx = checkpoint["class_to_idx"]
                class_names = [name for name, _ in sorted(class_to_idx.items(), key=lambda item: item[1])]

            for key in ["model_state_dict", "state_dict", "model"]:
                if key in checkpoint:
                    state_dict = checkpoint[key]
                    break

        if hasattr(state_dict, "state_dict"):
            state_dict = state_dict.state_dict()

        if isinstance(state_dict, dict):
            state_dict = {
                str(k).replace("module.", "", 1): v
                for k, v in state_dict.items()
            }

        num_classes = len(class_names or SRS_PAGE_CLASSES)
        if isinstance(state_dict, dict) and "fc.weight" in state_dict:
            num_classes = int(state_dict["fc.weight"].shape[0])

        if class_names is None:
            class_names = SRS_PAGE_CLASSES[:num_classes]
            if len(class_names) < num_classes:
                class_names = [f"page_type_{i}" for i in range(num_classes)]

        model = models.resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
        model.load_state_dict(state_dict, strict=False)
        model.eval()

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        SRS_RESNET_CACHE.update({
            "loaded": True,
            "model": model,
            "transform": transform,
            "classes": class_names,
            "status": "trained_resnet_loaded",
            "error": None,
        })
        return SRS_RESNET_CACHE

    except Exception as e:
        SRS_RESNET_CACHE.update({
            "loaded": True,
            "status": "resnet_load_failed",
            "error": str(e),
        })
        return SRS_RESNET_CACHE


def _predict_srs_page_with_resnet(image, fallback_text="", filename=""):
    cache = _load_srs_resnet_classifier()

    if cache.get("model") is not None and cache.get("transform") is not None:
        try:
            import torch

            image = image.convert("RGB")
            tensor = cache["transform"](image).unsqueeze(0)

            with torch.no_grad():
                logits = cache["model"](tensor)
                probs = torch.softmax(logits, dim=1)[0]
                index = int(torch.argmax(probs).item())
                confidence = round(float(probs[index].item()), 4)

            classes = cache.get("classes") or SRS_PAGE_CLASSES
            predicted_label = classes[index] if index < len(classes) else f"page_type_{index}"

            return {
                "predicted_page_type": predicted_label,
                "display_page_type": _humanize_page_type(predicted_label),
                "confidence": confidence,
                "source": "trained_resnet18_checkpoint",
                "resnet_status": cache.get("status"),
                "explanation": "Prediction produced by the deployed ResNet18 page classifier checkpoint.",
            }

        except Exception as e:
            fallback_label, fallback_conf, explanation = _heuristic_srs_page_type(fallback_text, filename)
            return {
                "predicted_page_type": fallback_label,
                "display_page_type": _humanize_page_type(fallback_label),
                "confidence": fallback_conf,
                "source": "fallback_after_resnet_prediction_error",
                "resnet_status": "resnet_prediction_failed",
                "resnet_error": str(e),
                "explanation": explanation,
            }

    fallback_label, fallback_conf, explanation = _heuristic_srs_page_type(fallback_text, filename)
    return {
        "predicted_page_type": fallback_label,
        "display_page_type": _humanize_page_type(fallback_label),
        "confidence": fallback_conf,
        "source": "fallback_text_heuristic",
        "resnet_status": cache.get("status"),
        "resnet_error": cache.get("error"),
        "explanation": explanation,
    }


def classify_uploaded_srs_visual(file_path, extracted_text="", original_filename=""):
    """
    Classify the uploaded image/PDF page type for the current evaluation.
    This is different from the notebook summary: it gives a prediction for the user's file.
    """
    ext = os.path.splitext(file_path)[1].lower()
    visual_exts = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}

    if ext not in visual_exts:
        return None

    page_predictions = []

    try:
        if ext == ".pdf":
            import fitz
            from SRS.srs_engine.document_parser import render_pdf_page_to_image

            doc = fitz.open(file_path)
            max_pages = min(len(doc), 5)
            doc.close()

            for page_index in range(max_pages):
                image = render_pdf_page_to_image(file_path, page_index, zoom=2.0)
                prediction = _predict_srs_page_with_resnet(
                    image,
                    fallback_text=extracted_text,
                    filename=original_filename,
                )
                prediction["page_number"] = page_index + 1
                page_predictions.append(prediction)

        else:
            from PIL import Image

            image = Image.open(file_path).convert("RGB")
            prediction = _predict_srs_page_with_resnet(
                image,
                fallback_text=extracted_text,
                filename=original_filename,
            )
            prediction["page_number"] = 1
            page_predictions.append(prediction)

    except Exception as e:
        fallback_label, fallback_conf, explanation = _heuristic_srs_page_type(extracted_text, original_filename)
        page_predictions.append({
            "page_number": 1,
            "predicted_page_type": fallback_label,
            "display_page_type": _humanize_page_type(fallback_label),
            "confidence": fallback_conf,
            "source": "fallback_after_visual_processing_error",
            "resnet_status": "visual_processing_failed",
            "resnet_error": str(e),
            "explanation": explanation,
        })

    page_type_distribution = {}
    for prediction in page_predictions:
        label = prediction.get("predicted_page_type", "unknown")
        page_type_distribution[label] = page_type_distribution.get(label, 0) + 1

    main_prediction = page_predictions[0] if page_predictions else {}

    return {
        "available": True,
        "model": "ResNet18 / CV page classifier",
        "description": "Classification of the currently uploaded image or PDF pages.",
        "input_file": original_filename or os.path.basename(file_path),
        "input_type": "pdf" if ext == ".pdf" else "image",
        "overall_uploaded_document_type": main_prediction.get("predicted_page_type"),
        "overall_uploaded_document_type_display": main_prediction.get("display_page_type"),
        "confidence": main_prediction.get("confidence"),
        "source": main_prediction.get("source"),
        "resnet_status": main_prediction.get("resnet_status"),
        "resnet_error": main_prediction.get("resnet_error"),
        "page_type_distribution": page_type_distribution,
        "page_predictions": page_predictions,
    }

# Labels for predictions
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
STRESS_LABELS = ["not_stress", "stress"]
VOICE_EMOTION_LABELS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]  # 8-class audio emotion model

LEGAL_TEMPLATES_DIR = Path(BASE_DIR) / "templates"
LEGAL_OUTPUT_DIR = Path(BASE_DIR) / "generated" / "legal"
LEGAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_legal_intelligence = LegalDocumentIntelligence() if LEGAL_FEATURES_AVAILABLE else None
_template_generator = TemplateDocumentGenerator() if LEGAL_FEATURES_AVAILABLE else None

NUMERIC_POSTURE_COLS = [
    "eye_shoulder_y_ratio",
    "shoulder_y_diff",
    "wrist_distance_x",
    "wrist_shoulder_ratio",
    "nose_eye_center_offset_x",
    "shoulder_span",
    "hip_shoulder_y_diff",
    "body_lean_x",
    "shoulder_center_x",
    "hip_center_x",
    "spine_angle",
    "eye_distance",
    "head_tilt_angle",
    "eye_distance_ratio",
    "shoulder_slope",
]

HEAD_CLASSES = ["Center", "Looking Left", "Looking Right", "Looking Straight"]
ARM_CLASSES = ["Closed Arms", "Open Arms", "Partially Open"]
POSTURE_CLASSES = ["Leaning", "Stiff", "Upright"]

# MediaPipe landmark indices
NOSE = 0
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24

FACE_CASCADE_DEFAULT = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
FACE_CASCADE_ALT2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
FACE_DETECTOR = None

try:
    FACE_DETECTOR = mp.solutions.face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.35,
    )
except Exception as e:
    print(f"[WARN] MediaPipe face detector unavailable: {e}")

# Global models storage
models_loaded = {
    'emotion': None,
    'stress': None,
    'pose_detector': None,
    'confidence_model': None,
    'label_encoder': None,
    'scaler': None,
    'voice_emotion': None,
}


def find_model_path(*relative_paths):
    for relative_path in relative_paths:
        candidate_path = os.path.join(BASE_DIR, relative_path)
        if os.path.exists(candidate_path):
            return candidate_path
    return None


def _humanize_filename(stem: str) -> str:
    cleaned = re.sub(r"_updated.*$", "", stem, flags=re.IGNORECASE)
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else stem


def _legal_template_items() -> list[dict[str, Any]]:
    if not LEGAL_TEMPLATES_DIR.exists():
        return []

    items: list[dict[str, Any]] = []
    for template_path in sorted(LEGAL_TEMPLATES_DIR.iterdir()):
        if not template_path.is_file():
            continue
        if template_path.suffix.lower() not in {".docx", ".txt", ".md", ".pdf", ".xlsx"}:
            continue

        template_text = _read_legal_document_text(template_path)
        placeholders = []
        seen_tokens: dict[str, int] = {}
        for match in re.finditer(r"\{([^{}]{2,80})\}|\[([^\[\]]{2,80})\]", template_text):
            raw = (match.group(1) or match.group(2) or "").strip()
            if not raw:
                continue
            cleaned = re.sub(r"\s+", " ", raw).strip(" .:-")
            if not cleaned or re.fullmatch(r"[\d\s.,%€$+-]+", cleaned):
                continue
            token = f"{{{match.group(1)}}}" if match.group(1) else f"[{match.group(2)}]"
            seen_tokens[token] = seen_tokens.get(token, 0) + 1
            occurrence_index = seen_tokens[token]
            label = cleaned.title() if cleaned.islower() else cleaned
            placeholders.append(
                {
                    "label": label,
                    "token": token,
                    "occurrence": occurrence_index,
                    "name": f"{re.sub(r'[^A-Za-z0-9]+', '_', label).strip('_').lower()}_{occurrence_index}",
                }
            )

        items.append(
            {
                "id": template_path.stem,
                "name": _humanize_filename(template_path.stem),
                "file_name": template_path.name,
                "extension": template_path.suffix.lower().lstrip("."),
                "path": str(template_path),
                "template": template_text,
                "placeholders": [item["label"] for item in placeholders],
                "fields": [
                    {
                        "name": item["name"],
                        "label": item["label"],
                        "type": "textarea" if len(item["label"]) > 30 else "text",
                        "required": True,
                        "sourceToken": item["token"],
                    }
                    for item in placeholders
                ],
            }
        )

    return items


def _read_legal_document_text(document_path: Path) -> str:
    suffix = document_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return document_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        document = Document(str(document_path))
        parts: list[str] = []
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                parts.append(paragraph.text.strip())
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            parts.append(paragraph.text.strip())
        return "\n".join(parts).strip()
    if suffix == ".pdf":
        extracted_text = ""
        parts: list[str] = []

        if PdfReader is not None:
            try:
                reader = PdfReader(str(document_path))
                for page in reader.pages:
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""
                    if text.strip():
                        parts.append(text)
            except Exception:
                parts = []

        extracted_text = "\n".join(parts).strip()

        if not extracted_text:
            try:
                import fitz

                pdf_doc = fitz.open(str(document_path))
                fitz_parts: list[str] = []
                for page in pdf_doc:
                    try:
                        page_text = page.get_text("text") or ""
                    except Exception:
                        page_text = ""
                    if page_text.strip():
                        fitz_parts.append(page_text)
                extracted_text = "\n".join(fitz_parts).strip()
            except Exception:
                extracted_text = extracted_text or ""

        # If text extraction still failed, try OCR as a last resort.
        if not extracted_text and _legal_intelligence is not None:
            try:
                import fitz
                from PIL import Image

                pdf_doc = fitz.open(str(document_path))
                ocr_parts: list[str] = []
                for page_num, page in enumerate(pdf_doc):
                    if page_num > 10:  # Limit to first 10 pages for performance
                        break
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    img_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                    img.save(img_path)
                    try:
                        page_text = _legal_intelligence._load_image_text(img_path)  # noqa: SLF001
                        if page_text:
                            ocr_parts.append(page_text)
                    finally:
                        try:
                            os.unlink(img_path)
                        except Exception:
                            pass
                if ocr_parts:
                    extracted_text = "\n".join(ocr_parts).strip()
            except Exception:
                pass

        return extracted_text
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"} and _legal_intelligence is not None:
        return _legal_intelligence._load_image_text(str(document_path))  # noqa: SLF001
    return document_path.read_text(encoding="utf-8", errors="ignore")


def _build_template_value_map(template_name: str, values: dict[str, object]) -> tuple[Path, dict[str, object]]:
    """Build template value map matching integ's approach.
    
    Maps frontend field-name keyed `values` to template token-keyed dict.
    Handles list values and properly merges multiple occurrences of the same token.
    Only includes tokens that have actual values (not empty/None).
    """
    templates_dir = LEGAL_TEMPLATES_DIR
    template_path = templates_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    templates = _legal_template_items()
    template_meta = next((item for item in templates if item.get("file_name") == template_name or item.get("id") == template_name), None)
    if template_meta is None:
        raise FileNotFoundError(f"Template metadata not found for: {template_name}")

    field_lookup = {field["name"]: field for field in template_meta.get("fields", []) if isinstance(field, dict)}
    token_values: dict[str, list[str] | str] = {}

    for field_name, field_value in values.items():
        field = field_lookup.get(field_name)
        if not field:
            continue
        token = field.get("sourceToken")
        if not token:
            continue
        
        # Skip empty/None values - don't add them to the map
        if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
            continue

        if isinstance(field_value, list):
            current = token_values.get(token)
            if not isinstance(current, list):
                current = []
            current.extend([str(item) for item in field_value if item is not None])
            token_values[token] = current
        else:
            current = token_values.get(token)
            if isinstance(current, list):
                current.append(str(field_value))
            elif current is None:
                token_values[token] = str(field_value)
            else:
                token_values[token] = [str(current), str(field_value)]

    return template_path, token_values


def _build_docx_from_text(content: str, output_path: Path, title: str | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()

    if title:
        document.add_heading(title, level=1)

    paragraphs = [paragraph for paragraph in content.splitlines()]
    if not paragraphs:
        document.add_paragraph("")
    else:
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)

    document.save(str(output_path))
    return output_path


def _convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise RuntimeError("LibreOffice is required to export PDF files")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp_dir, str(docx_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        converted_pdf = Path(tmp_dir) / f"{docx_path.stem}.pdf"
        if not converted_pdf.exists():
            raise RuntimeError("PDF export failed")
        pdf_path.write_bytes(converted_pdf.read_bytes())

    return pdf_path


def _extract_request_text(default_name: str = "uploaded document") -> tuple[str, str | None, dict | None]:
    if request.content_type and request.content_type.startswith("multipart"):
        uploaded_file = request.files.get("file")
        if uploaded_file is None:
            raise ValueError("No file uploaded")

        suffix = Path(uploaded_file.filename or "").suffix or ".txt"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            uploaded_file.save(temp_file.name)
            source_path = Path(temp_file.name)
            # If the uploaded file is an image, run OCR and save annotated images
            ocr_result = None
            if suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                try:
                    from ocr.document_analyzer import DocumentAnalyzer

                    analyzer = DocumentAnalyzer()
                    annotated_path = LEGAL_OUTPUT_DIR / f"{source_path.stem}_ocr_annotated.png"
                    ocr_result = analyzer.analyze(str(source_path), save_annotated_to=str(annotated_path))

                    # If signatures detected, produce a signature-only annotated image
                    sigs = ocr_result.get("signatures") or []
                    if sigs:
                        try:
                            import cv2 as _cv2

                            img = _cv2.imread(str(source_path))
                            if img is not None:
                                for s in sigs:
                                    box = s.get("box") or s.get("bbox") or None
                                    if not box or len(box) < 4:
                                        continue
                                    x, y, w, h = map(int, box[:4])
                                    _cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                sig_path = LEGAL_OUTPUT_DIR / f"{source_path.stem}_signatures.png"
                                _cv2.imwrite(str(sig_path), img)
                                ocr_result["signature_annotated_image_path"] = str(sig_path)
                        except Exception:
                            pass

                except Exception:
                    ocr_result = None

            # Read text content from the uploaded file (text/pdf/docx/image->ocr text)
            text = _read_legal_document_text(source_path)
            return text, uploaded_file.filename or default_name, ocr_result
        finally:
            temp_file.close()
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or payload.get("content") or "").strip()
    source_name = str(payload.get("source_name") or payload.get("name") or default_name).strip() or default_name
    if not text:
        raise ValueError("No text provided")
    return text, source_name, None


def dist(a, b):
    try:
        result = np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return result
    except Exception:
        return 0.0


def safe_angle(y, x):
    try:
        result = np.degrees(np.arctan2(y, x + 1e-6))
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return result
    except Exception:
        return 0.0


def one_hot(value, classes):
    return [1.0 if value == c else 0.0 for c in classes]


def find_best_face(gray):
    """Find the best face candidate using multiple cascade passes."""
    try:
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        if FACE_DETECTOR is not None:
            try:
                mp_result = FACE_DETECTOR.process(rgb)
                detections = getattr(mp_result, "detections", None) or []
                if detections:
                    h, w = gray.shape[:2]
                    best_detection = max(
                        detections,
                        key=lambda detection: detection.location_data.relative_bounding_box.width
                        * detection.location_data.relative_bounding_box.height,
                    )
                    bbox = best_detection.location_data.relative_bounding_box
                    x = max(0, int(bbox.xmin * w))
                    y = max(0, int(bbox.ymin * h))
                    bw = max(1, int(bbox.width * w))
                    bh = max(1, int(bbox.height * h))
                    return x, y, bw, bh
            except Exception as e:
                print(f"[WARN] MediaPipe face detection fallback failed: {e}")

        variants = [
            (gray, 1.08, 4, 24),
            (cv2.equalizeHist(gray), 1.05, 3, 22),
        ]

        if gray.shape[1] >= 320 and gray.shape[0] >= 240:
            enlarged = cv2.resize(gray, None, fx=1.25, fy=1.25, interpolation=cv2.INTER_LINEAR)
            variants.append((cv2.equalizeHist(enlarged), 1.03, 3, 20))

        best_face = None
        best_area = 0

        for source, scale_factor, min_neighbors, min_size in variants:
            for cascade in (FACE_CASCADE_DEFAULT, FACE_CASCADE_ALT2):
                if cascade.empty():
                    continue

                faces = cascade.detectMultiScale(
                    source,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(min_size, min_size),
                )

                if len(faces) == 0:
                    continue

                scale_x = gray.shape[1] / source.shape[1]
                scale_y = gray.shape[0] / source.shape[0]

                for x, y, w, h in faces:
                    area = w * h
                    if area <= best_area:
                        continue

                    best_area = area
                    best_face = (
                        int(x * scale_x),
                        int(y * scale_y),
                        int(w * scale_x),
                        int(h * scale_y),
                    )

        return best_face
    except Exception as e:
        print(f"[WARN] find_best_face failed: {e}")
        return None


def compute_posture_features(landmarks):
    try:
        if not landmarks or len(landmarks) < 33:
            return None

        LS = landmarks[LEFT_SHOULDER]
        RS = landmarks[RIGHT_SHOULDER]
        LH = landmarks[LEFT_HIP]
        RH = landmarks[RIGHT_HIP]
        LW = landmarks[LEFT_WRIST]
        RW = landmarks[RIGHT_WRIST]
        LE = landmarks[LEFT_EAR]
        RE = landmarks[RIGHT_EAR]
        nose_lm = landmarks[NOSE]

        shoulder_center_x = (LS.x + RS.x) / 2
        shoulder_center_y = (LS.y + RS.y) / 2
        hip_center_x = (LH.x + RH.x) / 2
        hip_center_y = (LH.y + RH.y) / 2
        eye_center_x = (LE.x + RE.x) / 2
        eye_center_y = (LE.y + RE.y) / 2

        shoulder_span = dist(LS, RS)
        eye_distance = dist(LE, RE)
        wrist_distance_x = abs(LW.x - RW.x)

        shoulder_y_diff = abs(LS.y - RS.y)
        shoulder_slope = shoulder_y_diff / (abs(LS.x - RS.x) + 1e-6)
        hip_shoulder_y_diff = abs(hip_center_y - shoulder_center_y)
        body_lean_x = shoulder_center_x - hip_center_x

        spine_angle = safe_angle(hip_center_y - shoulder_center_y, shoulder_center_x - hip_center_x)
        head_tilt_angle = safe_angle(nose_lm.y - eye_center_y, nose_lm.x - eye_center_x)

        eye_shoulder_y_ratio = (eye_center_y - shoulder_center_y) / (shoulder_span + 1e-6)
        wrist_shoulder_ratio = wrist_distance_x / (shoulder_span + 1e-6)
        nose_eye_center_offset_x = nose_lm.x - eye_center_x
        eye_distance_ratio = eye_distance / (shoulder_span + 1e-6)

        if abs(nose_eye_center_offset_x) < 0.025:
            head_direction = "Looking Straight"
        elif nose_eye_center_offset_x > 0:
            head_direction = "Looking Right"
        else:
            head_direction = "Looking Left"

        if wrist_shoulder_ratio > 1.35:
            arm_position = "Open Arms"
        elif wrist_shoulder_ratio < 0.75:
            arm_position = "Closed Arms"
        else:
            arm_position = "Partially Open"

        if abs(body_lean_x) > 0.05:
            posture = "Leaning"
        elif shoulder_y_diff > 0.03:
            posture = "Stiff"
        else:
            posture = "Upright"

        return {
            "eye_shoulder_y_ratio": eye_shoulder_y_ratio,
            "shoulder_y_diff": shoulder_y_diff,
            "wrist_distance_x": wrist_distance_x,
            "wrist_shoulder_ratio": wrist_shoulder_ratio,
            "nose_eye_center_offset_x": nose_eye_center_offset_x,
            "shoulder_span": shoulder_span,
            "hip_shoulder_y_diff": hip_shoulder_y_diff,
            "body_lean_x": body_lean_x,
            "shoulder_center_x": shoulder_center_x,
            "hip_center_x": hip_center_x,
            "spine_angle": spine_angle,
            "eye_distance": eye_distance,
            "head_tilt_angle": head_tilt_angle,
            "eye_distance_ratio": eye_distance_ratio,
            "shoulder_slope": shoulder_slope,
            "head_direction": head_direction,
            "arm_position": arm_position,
            "posture": posture,
        }
    except Exception as e:
        print(f"[ERROR] compute_posture_features failed: {e}")
        traceback.print_exc()
        return None


def preprocess_posture_features(raw_feat):
    numeric = np.array([raw_feat[col] for col in NUMERIC_POSTURE_COLS], dtype=np.float32).reshape(1, -1)
    head_oh = np.array(one_hot(raw_feat["head_direction"], HEAD_CLASSES), dtype=np.float32).reshape(1, -1)
    arm_oh = np.array(one_hot(raw_feat["arm_position"], ARM_CLASSES), dtype=np.float32).reshape(1, -1)
    posture_oh = np.array(one_hot(raw_feat["posture"], POSTURE_CLASSES), dtype=np.float32).reshape(1, -1)

    if hasattr(models_loaded.get("scaler"), "n_features_in_") and models_loaded["scaler"].n_features_in_ == 15:
        numeric_scaled = models_loaded["scaler"].transform(numeric)
        final_vec = np.concatenate([numeric_scaled, head_oh, arm_oh, posture_oh], axis=1)
    else:
        full_vec = np.concatenate([numeric, head_oh, arm_oh, posture_oh], axis=1)
        if models_loaded.get("scaler") is not None:
            final_vec = models_loaded["scaler"].transform(full_vec)
        else:
            final_vec = full_vec

    return final_vec.astype(np.float32)


def convert_audio_to_wav(source_path, wav_path):
    """Convert an uploaded audio file to a mono WAV file."""
    audio_segment_module = importlib.import_module("pydub")
    audio = audio_segment_module.AudioSegment.from_file(source_path)
    audio = audio.set_channels(1).set_frame_rate(22050)
    audio.export(wav_path, format="wav")
    return wav_path

def load_models():
    """Load ML models"""
    try:
        emotion_path = find_model_path(
            "models/emotion_model.h5",
            "models/emotion/emotion_model.h5",
            "models/emotion/best_model_64.0pct.h5",
        )
        stress_path = find_model_path(
            "models/best_final_stress_cnn_73.h5",
            "models/stress/best_final_stress_cnn_73.h5",
        )
        
        if emotion_path:
            models_loaded['emotion'] = load_model(emotion_path)
            print("[OK] Emotion model loaded")
        else:
            print("[!] Emotion model not found in any expected location")
            
        if stress_path:
            models_loaded['stress'] = load_model(stress_path)
            print("[OK] Stress model loaded")
        else:
            print("[!] Stress model not found in any expected location")
        
        # Load pose detection model
        try:
            pose_task_path = find_model_path("models/posturedata/pose_landmarker.task")
            if pose_task_path:
                base_options = mp.tasks.BaseOptions(model_asset_path=pose_task_path)
                options = mp.tasks.vision.PoseLandmarkerOptions(base_options=base_options, output_segmentation_masks=False)
                models_loaded['pose_detector'] = mp.tasks.vision.PoseLandmarker.create_from_options(options)
                print("[OK] Pose detector loaded")
            else:
                print("[!] Pose landmarker task not found")
        except Exception as e:
            print(f"[!] Pose detector loading failed: {e}")
        
        # Load posture confidence model
        try:
            confidence_path = find_model_path("models/posturedata/confidence_model.pkl")
            if confidence_path:
                models_loaded['confidence_model'] = joblib.load(confidence_path)
                print("[OK] Confidence model loaded")
            else:
                print("[!] Confidence model not found - posture detection will use landmarks only")
        except Exception as e:
            print(f"[!] Confidence model loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load label encoder
        try:
            encoder_path = find_model_path("models/posturedata/label_encoder.pkl")
            if encoder_path:
                models_loaded['label_encoder'] = joblib.load(encoder_path)
                print("[OK] Label encoder loaded")
            else:
                print("[!] Label encoder not found")
        except Exception as e:
            print(f"[!] Label encoder loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load scaler
        try:
            scaler_path = find_model_path("models/posturedata/scaler.pkl")
            if scaler_path:
                models_loaded['scaler'] = joblib.load(scaler_path)
                print("[OK] Scaler loaded")
            else:
                print("[!] Scaler not found")
        except Exception as e:
            print(f"[!] Scaler loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load voice emotion model
        try:
            if os.path.exists(VOICE_EMOTION_MODEL_PATH):
                models_loaded['voice_emotion'] = load_model(VOICE_EMOTION_MODEL_PATH)
                print(f"[OK] Voice emotion model loaded from {VOICE_EMOTION_MODEL_PATH}")
            else:
                print(f"[!] Voice emotion model not found at {VOICE_EMOTION_MODEL_PATH}")
        except Exception as e:
            print(f"[!] Voice emotion model loading failed: {e}")
            
    except Exception as e:
        print(f"[ERROR] Error loading models: {e}")
        traceback.print_exc()


# -----------------
# Pitch deck routes
# -----------------
@app.route('/api/pitch/generate', methods=['POST'])
def api_generate_pitch():
    try:
        data = request.json or {}
        company = data.get('company', 'Your Startup')
        industry = data.get('industry', 'your industry')
        description = data.get('description', 'a clear solution to a real problem')

        import subprocess, json, sys
        script = os.path.join(BASE_DIR, "pitch_generator.py")
        result = subprocess.run(
            [sys.executable, script, company, industry, description],
            capture_output=True, text=True, timeout=600,
            cwd=BASE_DIR
        )
        
        print("[PitchGen stderr]", result.stderr[-1000:])
        print("[PitchGen stdout]", result.stdout[:500])
        
        if result.returncode != 0:
            return jsonify({'error': result.stderr[-500:]}), 500

        # Trouve le JSON dans stdout (ignore les warnings avant)
        stdout = result.stdout.strip()
        json_start = stdout.rfind('{')
        json_end = stdout.rfind('}') + 1
        if json_start == -1:
            return jsonify({'error': 'No JSON in output', 'raw': stdout[:300]}), 500
        
        slides = json.loads(stdout[json_start:json_end])
        return jsonify({'slides': slides})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
            
@app.route('/api/pitch/download', methods=['POST'])
def api_download_pitch():
    try:
        data = request.json or {}
        company = data.get('company', 'Your Startup')
        industry = data.get('industry', 'your industry')
        description = data.get('description', 'a clear solution to a real problem')

        from pitch_generator import generate_all_slides, build_pptx

        slides = generate_all_slides(company, industry, description)
        # Save to temporary file
        fd, tmp_path = tempfile.mkstemp(suffix='.pptx')
        os.close(fd)
        build_pptx(company, industry, description, slides, tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name=f"{company}_pitch_deck.pptx")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def preprocess_face(face_array):
    """Preprocess face image for model prediction"""
    try:
        face = cv2.resize(face_array, (48, 48))
        face = face.astype(np.float32) / 255.0
        face = np.expand_dims(face, axis=-1)
        face = np.expand_dims(face, axis=0)
        return face
    except Exception as e:
        print(f"[ERROR] Error preprocessing face: {e}")
        return None

def detect_emotion(frame_base64):
    """Detect emotion from frame"""
    try:
        if models_loaded['emotion'] is None:
            return {"error": "Emotion model not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for emotion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        face = find_best_face(gray)

        if face is None:
            return {"emotion": "no_face", "confidence": 0.0, "face_detected": False}
        
        # Get largest face candidate
        x, y, w, h = face
        face_gray = gray[y:y+h, x:x+w]
        
        # Preprocess and predict
        preprocessed = preprocess_face(face_gray)
        if preprocessed is None:
            return {"error": "Preprocessing failed"}
        
        preds = models_loaded['emotion'].predict(preprocessed, verbose=0)[0]
        emotion_idx = int(np.argmax(preds))
        
        return {
            "emotion": EMOTION_LABELS[emotion_idx],
            "confidence": float(preds[emotion_idx]),
            "face_detected": True,
            "face_box": {
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            },
            "scores": {
                EMOTION_LABELS[i]: float(preds[i])
                for i in range(len(EMOTION_LABELS))
            }
        }
    except Exception as e:
        print(f"[ERROR] Error detecting emotion: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_stress(frame_base64):
    """Detect stress from frame"""
    try:
        if models_loaded['stress'] is None:
            return {"error": "Stress model not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        face = find_best_face(gray)

        if face is None:
            return {"stress": "unknown", "confidence": 0.0}
        
        # Get largest face candidate
        x, y, w, h = face
        face_gray = gray[y:y+h, x:x+w]
        
        # Preprocess and predict
        preprocessed = preprocess_face(face_gray)
        if preprocessed is None:
            return {"error": "Preprocessing failed"}
        
        preds = models_loaded['stress'].predict(preprocessed, verbose=0)[0]
        
        if len(preds) == 1:
            stress_prob = float(preds[0])
            label = "stressed" if stress_prob >= 0.5 else "not stressed"
            confidence = stress_prob if label == "stressed" else 1 - stress_prob
        else:
            stress_idx = int(np.argmax(preds))
            label = "stressed" if STRESS_LABELS[stress_idx] == "stress" else "not stressed"
            confidence = float(preds[stress_idx])
        
        return {
            "stress": label,
            "confidence": confidence,
            "face_detected": True,
            "face_box": {
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            },
        }
    except Exception as e:
        print(f"[ERROR] Error detecting stress: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_posture(frame_base64):
    """Detect posture from frame"""
    try:
        if models_loaded['pose_detector'] is None:
            return {"error": "Pose detector not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect pose
        detection_result = models_loaded['pose_detector'].detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return {"posture": "unknown", "confidence": 0.0, "arm_position": "unknown", "head_direction": "unknown"}
        
        # Extract landmarks
        landmarks = detection_result.pose_landmarks[0]

        raw_feat = compute_posture_features(landmarks)
        if raw_feat is None:
            return {"posture": "unknown", "confidence": 0.0, "arm_position": "unknown", "head_direction": "unknown", "landmarks_count": len(landmarks)}

        confidence = 0.0
        posture_label = raw_feat["posture"]

        if models_loaded['confidence_model'] is not None:
            try:
                feat_vec = preprocess_posture_features(raw_feat)
                if hasattr(models_loaded['confidence_model'], 'predict_proba'):
                    probs = models_loaded['confidence_model'].predict_proba(feat_vec)[0]
                    prediction = int(np.argmax(probs))
                    confidence = float(np.max(probs))
                else:
                    prediction = int(models_loaded['confidence_model'].predict(feat_vec)[0])
                    confidence = 0.85

                if models_loaded['label_encoder'] is not None:
                    posture_label = models_loaded['label_encoder'].inverse_transform([prediction])[0]
                else:
                    posture_label = str(prediction)
            except Exception as model_error:
                print(f"[WARN] Posture classifier fallback used: {model_error}")
                confidence = 0.0

        return {
            "posture": posture_label,
            "confidence": confidence,
            "arm_position": raw_feat["arm_position"],
            "head_direction": raw_feat["head_direction"],
            "landmarks_count": len(landmarks),
        }
    except Exception as e:
        print(f"[ERROR] Error detecting posture: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_voice_emotion(audio_base64):
    """Detect emotion from audio using CNN model"""
    try:
        if models_loaded['voice_emotion'] is None:
            return {"error": "Voice emotion model not loaded"}
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64.split(',')[1] if ',' in audio_base64 else audio_base64)
        
        # Load audio from bytes
        try:
            audio_stream = io.BytesIO(audio_data)
            y, sr = librosa.load(audio_stream, sr=16000)
        except Exception as e:
            print(f"[!] Librosa load failed: {e}, trying alternative")
            # If librosa fails, try alternative loading
            import soundfile as sf
            audio_stream = io.BytesIO(audio_data)
            y, sr = sf.read(audio_stream)
            y = np.array(y, dtype=np.float32)
        
        # Build a 3-channel spectrogram image that matches the model input shape (128x128x3)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, n_fft=2048, hop_length=512)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize and create 3 channels: base mel, delta, delta-delta
        mel_norm = (mel_spec_db - np.mean(mel_spec_db)) / (np.std(mel_spec_db) + 1e-8)
        delta = librosa.feature.delta(mel_norm)
        delta2 = librosa.feature.delta(mel_norm, order=2)

        spectrogram = np.stack([mel_norm, delta, delta2], axis=-1)
        spectrogram = cv2.resize(spectrogram.astype(np.float32), (128, 128), interpolation=cv2.INTER_AREA)
        mel_spec_input = np.expand_dims(spectrogram, axis=0)

        expected_shape = models_loaded['voice_emotion'].input_shape
        print(f"[VoiceEmotion] input shape={mel_spec_input.shape}, model expects={expected_shape}")
        
        # Predict
        preds = models_loaded['voice_emotion'].predict(mel_spec_input, verbose=0)[0]
        emotion_idx = int(np.argmax(preds))
        
        return {
            "emotion": VOICE_EMOTION_LABELS[emotion_idx],
            "confidence": float(preds[emotion_idx]),
            "scores": {
                VOICE_EMOTION_LABELS[i]: float(preds[i])
                for i in range(len(VOICE_EMOTION_LABELS))
            }
        }
    except Exception as e:
        print(f"[ERROR] Error detecting voice emotion: {e}")
        traceback.print_exc()
        return {"error": str(e)}


# --- Marketing notebook helper functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_image_to_base64(image_path):
    try:
        with open(image_path, 'rb') as handle:
            return base64.b64encode(handle.read()).decode('utf-8')
    except Exception as exc:
        print(f"Error encoding image: {exc}")
        return None


def format_evaluation_for_display(eval_result):
    try:
        text_xai = eval_result.get('text_xai', {})
        full_ocr_text = (
            text_xai.get('raw_text_full')
            or eval_result.get('extracted_text')
            or eval_result.get('text_features', {}).get('raw_text', '')
            or eval_result.get('ocr_regions', {}).get('full_text', '')
            or ''
        )
        preview_ocr_text = text_xai.get('raw_text_preview') or full_ocr_text[:500]

        selected_platform = eval_result.get('platform_used_for_text_evaluation') or eval_result.get('platform') or 'unknown'
        platform_display = (selected_platform or 'unknown').upper()

        def safe_score(val, default=0):
            if val is None:
                return float(default)
            return float(val)

        text_score = safe_score(eval_result.get('text_evaluation', {}).get('overall_score', 0))
        visual_features = eval_result.get('visual_features', {})
        visual_xai = eval_result.get('visual_xai', {})
        visual_score = safe_score(
            visual_features.get('score_0_10', visual_xai.get('visual_prediction', {}).get('score_0_10', 0))
        )
        overall_score = safe_score(eval_result.get('overall_evaluation', {}).get('overall_score_0_10', 0))

        if visual_score < 3.33:
            fallback_visual_class = 'bad'
        elif visual_score < 6.67:
            fallback_visual_class = 'average'
        else:
            fallback_visual_class = 'good'

        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'platform_selected': platform_display,
            'text_evaluation': {
                'overall_score': round(text_score, 1),
                'penalized_overall_score': round(text_xai.get('penalized_overall_score', text_score), 1),
                'dimensions': eval_result.get('text_evaluation', {}).get('dimension_scores', {}),
                'ocr_text': preview_ocr_text,
                'ocr_text_full': full_ocr_text,
                'text_length': len(full_ocr_text),
                'sentiment': eval_result.get('text_evaluation', {}).get('sentiment_detail', {}),
                'issues': eval_result.get('text_evaluation', {}).get('issues', {}),
            },
            'visual_evaluation': {
                'overall_score': round(visual_score, 1),
                'class_label': visual_features.get('class_label') or fallback_visual_class,
                'score_band': visual_features.get('class_label') or fallback_visual_class,
                'confidence': visual_features.get('confidence', 0.0),
                'class_probs': visual_features.get('class_probs', {}),
                'model_source': visual_features.get('model_source', '') or visual_xai.get('score_source', ''),
                'visual_features': visual_features.get('visual_features', {}),
                'xai_summary': eval_result.get('visual_xai', {}).get('interpretation', ''),
                'composition': eval_result.get('visual_xai', {}).get('image_composition', {}),
                'extracted_image': eval_result.get('extracted_image_b64', None),
            },
            'text_xai': {
                'interpretation': text_xai.get('interpretation', ''),
                'overall_score': text_xai.get('overall_score', 0.0),
                'penalized_overall_score': text_xai.get('penalized_overall_score', 0.0),
                'universal_score': text_xai.get('universal_score', 0.0),
                'penalty_applied': text_xai.get('penalty_applied', 0.0),
                'dimension_scores': text_xai.get('dimension_scores', {}),
                'ranked_dimensions': text_xai.get('ranked_dimensions', []),
                'top_features': text_xai.get('top_features', {}),
                'issues_detected': text_xai.get('issues_detected', {}),
                'feature_metrics': text_xai.get('feature_metrics', {}),
            },
            'visual_xai': {
                'interpretation': visual_xai.get('interpretation', ''),
                'grad_cam': visual_xai.get('grad_cam', {}),
                'attribute_importance': visual_xai.get('attribute_importance_inference', {}),
                'visual_prediction': visual_xai.get('visual_prediction', {}),
                'image_composition': visual_xai.get('image_composition', {}),
            },
            'overall_engagement': {
                'score': round(overall_score, 1),
                'verdict': eval_result.get('overall_evaluation', {}).get('verdict', 'Unknown'),
                'breakdown': eval_result.get('overall_evaluation', {}).get('breakdown', {}),
            },
        }
        return result
    except Exception as exc:
        print(f"Error formatting evaluation: {exc}")
        traceback.print_exc()
        return {'success': False, 'error': str(exc)}


def get_verdict_color(score):
    if score is None:
        score = 0.0
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0

    if score >= 8.0:
        return 'verdict-excellent'
    if score >= 6.0:
        return 'verdict-good'
    if score >= 4.0:
        return 'verdict-mid'
    if score >= 2.0:
        return 'verdict-poor'
    return 'verdict-bad'


def _load_json_from_marketing_outputs(filename):
    path = Path(MARKETING_OUTPUTS_DIR) / filename
    if not path.exists():
        return {}
    try:
        with path.open('r', encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return {}


def analyze_marketing_screenshot(image_path, platform=None):
    """Notebook-style marketing analysis adapted into the backend."""
    outputs_dir = MARKETING_OUTPUTS_DIR
    platform_key = (platform or 'linkedin').lower()

    try:
        engagement_pipeline_path = os.path.join(MARKETING_NOTEBOOK_DIR, 'engagement_pipeline.py')
        pipeline_spec = importlib.util.spec_from_file_location('scaleup_marketing_engagement_pipeline', engagement_pipeline_path)
        if pipeline_spec is None or pipeline_spec.loader is None:
            raise ImportError(f'Could not load marketing pipeline from {engagement_pipeline_path}')

        pipeline_module = importlib.util.module_from_spec(pipeline_spec)
        pipeline_spec.loader.exec_module(pipeline_module)
        predict_engagement_from_screenshot = pipeline_module.predict_engagement_from_screenshot

        result = predict_engagement_from_screenshot(
            screenshot_path=image_path,
            outputs_dir=outputs_dir,
            metadata={'platform': platform_key},
            do_extract_image=True,
            include_legacy_model=False,
        )
        result['platform'] = result.get('platform') or platform_key
        result['timestamp'] = datetime.now().isoformat()
        return result
    except Exception as exc:
        raise RuntimeError(f"Live marketing pipeline failed: {exc}") from exc

# ========================
# API ENDPOINTS
# ========================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "models_loaded": {
            "emotion": models_loaded['emotion'] is not None,
            "stress": models_loaded['stress'] is not None,
            "posture": models_loaded['pose_detector'] is not None,
            "voice_emotion": models_loaded['voice_emotion'] is not None,
        }
    })

@app.route('/api/analyze/emotion', methods=['POST'])
def analyze_emotion():
    """Analyze emotion from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_emotion(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/stress', methods=['POST'])
def analyze_stress():
    """Analyze stress from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_stress(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/posture', methods=['POST'])
def analyze_posture():
    """Analyze posture from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_posture(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/voice-emotion', methods=['POST'])
def analyze_voice_emotion():
    """Analyze voice emotion from audio"""
    try:
        if request.content_type and request.content_type.startswith('multipart'):
            if 'file' not in request.files:
                return jsonify({"error": "No audio received"}), 400

            uploaded_file = request.files['file']
            raw_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            uploaded_file.save(raw_tmp.name)

            convert_audio_to_wav(raw_tmp.name, wav_tmp.name)

            if os.path.getsize(wav_tmp.name) < 1000:
                return jsonify({
                    "emotion": "no audio",
                    "confidence": 0,
                    "scores": {}
                })

            with open(wav_tmp.name, 'rb') as f:
                audio_payload = base64.b64encode(f.read()).decode('utf-8')
            result = detect_voice_emotion(audio_payload)
        else:
            data = request.json or {}
            audio_base64 = data.get('audio')

            if not audio_base64:
                return jsonify({"error": "No audio provided"}), 400

            result = detect_voice_emotion(audio_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze/speech-strength', methods=['POST'])
def analyze_speech_strength():
    """Analyze speech strength from audio (base64 or multipart file)"""
    try:
        # Accept JSON body with 'audio' (data URL) or multipart file
        if request.content_type and request.content_type.startswith('multipart'):
            # file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            f = request.files['file']
            raw_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            f.save(raw_tmp.name)

            convert_audio_to_wav(raw_tmp.name, wav_tmp.name)
            audio_path = wav_tmp.name
        else:
            data = request.get_json() or {}
            audio_b64 = data.get('audio')
            if not audio_b64:
                return jsonify({'error': 'No audio provided'}), 400
            # strip data URL prefix if present
            if ',' in audio_b64:
                audio_b64 = audio_b64.split(',', 1)[1]
            audio_bytes = base64.b64decode(audio_b64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            tmp.write(audio_bytes)
            tmp.flush()
            audio_path = tmp.name

        # Transcribe
        transcript = ""
        if transcribe_audio is not None:
            try:
                transcript = transcribe_audio(audio_path)
            except Exception:
                transcript = ""

        # Predict strength
        prediction = hybrid_strength_predict(transcript or "")
        bad_words = detect_bad_words(transcript or "")

        return jsonify({
            'transcript': transcript,
            'prediction': prediction,
            'bad_words': bad_words,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/marketing/analyze', methods=['POST'])
def analyze_marketing():
    """Analyze a marketing screenshot and return notebook-style outputs."""
    try:
        if 'screenshot' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        filename = secure_filename(file.filename)
        temp_dir = os.path.join(BASE_DIR, 'uploads')
        os.makedirs(temp_dir, exist_ok=True)
        saved_path = os.path.join(temp_dir, f"marketing_{filename}")
        file.save(saved_path)

        platform = (request.form.get('platform') or '').strip().lower() or None
        result = analyze_marketing_screenshot(saved_path, platform=platform)
        img_base64 = encode_image_to_base64(saved_path)

        try:
            os.remove(saved_path)
        except Exception:
            pass

        if result is None:
            return jsonify({'success': False, 'error': 'No result from marketing service'}), 500

        if 'success' not in result:
            try:
                formatted_result = format_evaluation_for_display(result)
                if not formatted_result.get('success'):
                    return jsonify({'success': False, 'error': formatted_result.get('error', 'Formatting failed')}), 500

                if img_base64:
                    formatted_result['image_base64'] = img_base64

                formatted_result['result_id'] = os.path.splitext(os.path.basename(saved_path))[0] + '_result'
                formatted_result['timestamp'] = datetime.now().isoformat()
                return jsonify(formatted_result), 200
            except Exception as exc:
                traceback.print_exc()
                return jsonify({'success': False, 'error': str(exc)}), 500

        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/legal/templates', methods=['GET'])
def legal_templates():
    if not LEGAL_FEATURES_AVAILABLE:
        return jsonify({'error': 'Legal features are unavailable'}), 503

    return jsonify({'templates': _legal_template_items()})


@app.route('/api/legal/infer', methods=['POST'])
def legal_infer_template_fields():
    if not LEGAL_FEATURES_AVAILABLE or IntelligentNDAFiller is None:
        return jsonify({'error': 'NDA inference is unavailable'}), 503

    try:
        payload = request.get_json(silent=True) or {}
        template_name = str(payload.get('file_name') or payload.get('template_name') or '').strip()
        brief_text = str(payload.get('brief_text') or payload.get('text') or '').strip()

        if not template_name:
            return jsonify({'error': 'No file_name provided'}), 400

        template_path = LEGAL_TEMPLATES_DIR / template_name
        if not template_path.exists():
            return jsonify({'error': f'Template not found: {template_name}'}), 404

        filler = IntelligentNDAFiller(str(template_path))
        hints = payload.get('hints') if isinstance(payload.get('hints'), dict) else {}
        report = filler.infer(brief_text, hints=hints)
        return jsonify({'report': report})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/legal/analyze', methods=['POST'])
def legal_analyze_document():
    if not LEGAL_FEATURES_AVAILABLE or _legal_intelligence is None:
        return jsonify({'error': 'Legal analysis is unavailable'}), 503

    try:
        text, source_name, ocr_result = _extract_request_text()
        question = None
        payload = request.get_json(silent=True) or {}
        if payload:
            question = str(payload.get('question') or '').strip() or None

        result = _legal_intelligence.analyze_text(text, source_name=source_name, question=question)

        # If OCR analysis was performed on an uploaded image, merge signatures and annotated images
        if ocr_result:
            # merge signatures from OCR (prefer analyzer signatures but append OCR if missing)
            ocr_sigs = ocr_result.get('signatures') or []
            if ocr_sigs:
                existing = result.get('signatures') or []
                # avoid duplicates by bounding box
                boxes = {tuple(s.get('box') or s.get('bbox') or []): True for s in existing}
                for s in ocr_sigs:
                    key = tuple(s.get('box') or s.get('bbox') or [])
                    if key and key not in boxes:
                        existing.append(s)
                result['signatures'] = existing

            # annotated images
            ann = ocr_result.get('annotated_image_path') or ocr_result.get('annotated_image')
            if ann:
                name = Path(str(ann)).name
                result['annotated_image_url'] = f"/generated/legal/{name}"
            sig_ann = ocr_result.get('signature_annotated_image_path')
            if sig_ann:
                name = Path(str(sig_ann)).name
                result['signature_annotated_image_url'] = f"/generated/legal/{name}"
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/document/intel-upload', methods=['POST'])
def document_intel_upload():
    if not LEGAL_FEATURES_AVAILABLE or _legal_intelligence is None:
        return jsonify({'error': 'Document intelligence is unavailable'}), 503

    try:
        text, source_name, ocr_result = _extract_request_text()
        question = str((request.form or {}).get('question') or '').strip() or None
        result = _legal_intelligence.analyze_text(text, source_name=source_name, question=question)
        result['source_name'] = source_name
        result['text'] = result.get('extractedText') or result.get('text') or text
        result['extractedText'] = result.get('text') or text
        result['document_kind'] = result.get('documentKind') or result.get('document_kind')
        result['summary_sources'] = result.get('summary_sources') or result.get('summarySources') or []
        result['extractive_summary'] = result.get('extractive_summary') or result.get('extractiveSummary') or ''
        result['domain_tags'] = result.get('domain_tags') or result.get('domainTags') or []
        result['risk_flags'] = result.get('risk_flags') or result.get('riskFlags') or []
        result['open_questions'] = result.get('open_questions') or result.get('openQuestions') or []
        # Normalize summary key(s)
        result['summary'] = (
            result.get('summary')
            or result.get('summary_text')
            or result.get('summaryText')
            or result.get('extractive_summary')
            or result.get('extractiveSummary')
            or ''
        )
        # Normalize detected signatures to a common key
        result['signatures'] = (
            result.get('signatures')
            or result.get('detected_signatures')
            or result.get('signature_rows')
            or result.get('signaturesDetected')
            or []
        )
        result['startup_signals'] = result.get('startup_signals') or result.get('startupSignals') or []
        result['key_clauses'] = result.get('key_clauses') or result.get('keyClauses') or []
        result['annotated_image_url'] = (
            result.get('annotated_image_url')
            or result.get('signature_annotated_image_url')
            or result.get('ocrAnnotatedImageUrl')
            or result.get('signatureAnnotatedImageUrl')
            or None
        )

        # merge OCR image results if we performed OCR during upload
        if ocr_result:
            ocr_sigs = ocr_result.get('signatures') or []
            if ocr_sigs:
                existing = result.get('signatures') or []
                boxes = {tuple(s.get('box') or s.get('bbox') or []): True for s in existing}
                for s in ocr_sigs:
                    key = tuple(s.get('box') or s.get('bbox') or [])
                    if key and key not in boxes:
                        existing.append(s)
                result['signatures'] = existing

            ann = ocr_result.get('annotated_image_path') or ocr_result.get('annotated_image')
            if ann and not result.get('annotated_image_url'):
                name = Path(str(ann)).name
                result['annotated_image_url'] = f"/generated/legal/{name}"
            sig_ann = ocr_result.get('signature_annotated_image_path')
            if sig_ann:
                name = Path(str(sig_ann)).name
                result['signature_annotated_image_url'] = f"/generated/legal/{name}"
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/legal/nda/infer', methods=['POST'])
def legal_infer_nda():
    if not LEGAL_FEATURES_AVAILABLE or IntelligentNDAFiller is None:
        return jsonify({'error': 'NDA inference is unavailable'}), 503

    try:
        payload = request.get_json(silent=True) or {}
        brief_text = str(payload.get('brief_text') or payload.get('text') or '').strip()
        if not brief_text:
            return jsonify({'error': 'No brief_text provided'}), 400

        template_name = str(payload.get('template_name') or '').strip()
        template_path = Path(payload.get('template_path') or '') if payload.get('template_path') else None
        if template_path is None and template_name:
            candidate = LEGAL_TEMPLATES_DIR / template_name
            if candidate.exists():
                template_path = candidate

        filler_template = template_path if template_path is not None and template_path.is_file() else (LEGAL_TEMPLATES_DIR / '__missing_template__.docx')
        filler = IntelligentNDAFiller(str(filler_template))
        hints = payload.get('hints') if isinstance(payload.get('hints'), dict) else {}
        result = filler.infer(brief_text, hints=hints)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/legal/generate', methods=['POST'])
def legal_generate_document():
    if not LEGAL_FEATURES_AVAILABLE or _template_generator is None:
        return jsonify({'error': 'Legal generation is unavailable'}), 503

    try:
        payload = request.get_json(silent=True) or {}
        template_name = str(payload.get('template_name') or '').strip()
        values = payload.get('values') if isinstance(payload.get('values'), dict) else {}
        if not template_name:
            return jsonify({'error': 'No template_name provided'}), 400

        template_path = LEGAL_TEMPLATES_DIR / template_name
        if not template_path.exists():
            return jsonify({'error': f'Template not found: {template_name}'}), 404

        output_name = payload.get('output_name') or f"{template_path.stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.docx"
        output_path = LEGAL_OUTPUT_DIR / str(output_name)
        remove_clause_numbers = payload.get('remove_clause_numbers')

        # Build template value map using integ's approach
        if values:
            try:
                _, token_values = _build_template_value_map(template_path.name, values)
            except Exception:
                token_values = {}
        else:
            token_values = {}

        generated_path = _template_generator.generate(
            str(template_path),
            str(output_path),
            token_values,
            strict=bool(payload.get('strict', False)),  # Default to False to allow partial fills
            strip_bracket_artifacts=bool(payload.get('strip_bracket_artifacts', True)),
            remove_clause_numbers=remove_clause_numbers,
        )

        if payload.get('download', True):
            return send_file(str(generated_path), as_attachment=True, download_name=Path(generated_path).name)

        return jsonify({'path': str(generated_path), 'file_name': Path(generated_path).name})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/legal/export', methods=['POST'])
def legal_export_document():
    if not LEGAL_FEATURES_AVAILABLE:
        return jsonify({'error': 'Legal generation is unavailable'}), 503

    try:
        payload = request.get_json(silent=True) or {}
        title = str(payload.get('title') or payload.get('file_name') or 'document').strip() or 'document'
        format_name = str(payload.get('format') or 'docx').strip().lower()
        file_name = str(payload.get('file_name') or '').strip()
        values = payload.get('values') if isinstance(payload.get('values'), dict) else {}
        remove_clause_numbers = payload.get('remove_clause_numbers')

        if format_name not in {'docx', 'pdf'}:
            return jsonify({'error': 'Unsupported export format'}), 400

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_") or 'document'
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        export_dir = LEGAL_OUTPUT_DIR / 'exports'
        export_dir.mkdir(parents=True, exist_ok=True)

        if file_name and values:
            try:
                template_path, token_values = _build_template_value_map(file_name, values)
            except Exception as e:
                return jsonify({'error': f'Template mapping failed: {str(e)}'}), 400

            docx_output = export_dir / f"{safe_name}_{timestamp}.docx"
            generated_docx = _template_generator.generate(
                str(template_path),
                str(docx_output),
                token_values,
                strict=False,  # Allow partial fills
                strip_bracket_artifacts=True,
                remove_clause_numbers=remove_clause_numbers,
            )

            if format_name == 'pdf':
                generated_path = _convert_docx_to_pdf(Path(generated_docx), Path(generated_docx).with_suffix('.pdf'))
            else:
                generated_path = Path(generated_docx)
        else:
            content = str(payload.get('content') or '').strip()
            if format_name == 'pdf':
                docx_output = export_dir / f"{safe_name}_{timestamp}.docx"
                generated_docx = _build_docx_from_text(content, docx_output, title=title)
                generated_path = _convert_docx_to_pdf(generated_docx, generated_docx.with_suffix('.pdf'))
            else:
                generated_path = _build_docx_from_text(content, export_dir / f"{safe_name}_{timestamp}.docx", title=title)

        download_url = f"/generated/legal/{generated_path.name}"
        return jsonify({'download_url': download_url, 'file_name': Path(generated_path).name})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/generated/legal/<path:filename>', methods=['GET'])
def serve_generated_legal_file(filename: str):
    candidates = [LEGAL_OUTPUT_DIR / filename, LEGAL_OUTPUT_DIR / 'exports' / filename]
    for candidate in candidates:
        if candidate.exists():
            return send_file(str(candidate), as_attachment=True, download_name=candidate.name)
    return jsonify({'error': 'File not found'}), 404


def _load_signature_model_torch(selection_key: str = ""):
    """Load PyTorch signature classification model."""
    try:
        import torch
        import torch.nn as nn
        from torchvision import models, transforms
        
        scripted_candidates = [
            Path(BASE_DIR) / "signature_best_script.pt",
            Path(BASE_DIR) / "signature_resnet18_script.pt",
            Path(BASE_DIR) / "signature_cnn_script.pt",
            Path(BASE_DIR) / "models/legal/signature_best_script.pt",
            Path(BASE_DIR) / "models/legal/signature_resnet18_script.pt",
            Path(BASE_DIR) / "models/legal/signature_cnn_script.pt",
        ]
        
        for model_path in scripted_candidates:
            if model_path.exists():
                try:
                    model = torch.jit.load(str(model_path), map_location="cpu")
                    model.eval()
                    if "cnn" in model_path.name.lower():
                        transform = transforms.Compose([
                            transforms.Grayscale(num_output_channels=1),
                            transforms.Resize((128, 256)),
                            transforms.ToTensor(),
                            transforms.Normalize([0.5], [0.5])
                        ])
                    else:
                        transform = transforms.Compose([
                            transforms.Resize((224, 224)),
                            transforms.ToTensor(),
                            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                        ])
                    return model, transform, model_path
                except Exception:
                    continue
    except Exception:
        pass
    
    return None, None, None


def _load_signature_detector_yolo(selection_key: str = ""):
    """Load YOLO signature detection model."""
    try:
        from ultralytics import YOLO
        
        candidates = [
            Path(BASE_DIR) / "data2/chekpoint_last.pt",
            Path(BASE_DIR) / "runs/detect/signature_yolo_clean/weights/best.pt",
        ]
        
        for model_path in candidates:
            if model_path.exists():
                try:
                    return YOLO(str(model_path)), model_path
                except Exception:
                    continue
    except Exception:
        pass
    
    return None, None


@app.route('/api/signature/predict', methods=['POST'])
def predict_signature_api():
    """Predict whether signature is fake or real using torch model."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Missing file"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Missing uploaded filename"}), 400

        try:
            import torch
            from PIL import Image as PILImage
        except ImportError:
            return jsonify({"error": "PyTorch not available"}), 503

        model, transform, model_path = _load_signature_model_torch()
        if model is None or transform is None:
            return jsonify({"error": "Signature model not found"}), 503

        contents = file.read()
        img = PILImage.open(io.BytesIO(contents)).convert('RGB')
        img_tensor = transform(img).unsqueeze(0)
        
        with torch.no_grad():
            out = model(img_tensor)
            probs = torch.softmax(out, dim=1)[0].cpu().numpy().tolist()
            pred = out.argmax(1).item()
        
        label = 'fake' if pred == 0 else 'real'
        return jsonify({
            "prediction": label,
            "prediction_confidence": float(probs[pred]),
            "class_probabilities": {
                "fake": float(probs[0]),
                "real": float(probs[1]),
            },
            "model": model_path.name if model_path else "unknown",
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/signature/detect', methods=['POST'])
def detect_signature_api():
    """Detect signature bounding boxes using YOLO model."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Missing file"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Missing uploaded filename"}), 400

        conf = float(request.form.get('conf', 0.25))
        iou = float(request.form.get('iou', 0.45))
        
        model, model_path = _load_signature_detector_yolo()
        if model is None:
            return jsonify({"error": "YOLO model not found"}), 503

        try:
            from PIL import Image as PILImage
        except ImportError:
            return jsonify({"error": "PIL not available"}), 503

        contents = file.read()
        image = PILImage.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image)

        results = model.predict(source=image_np, conf=conf, iou=iou, verbose=False)
        if not results:
            return jsonify({
                "model": model_path.name if model_path else "unknown",
                "count": 0,
                "detections": [],
                "annotated_image_url": None,
            })

        result = results[0]
        detections: list[dict[str, Any]] = []
        names = result.names or {}

        if result.boxes is not None and len(result.boxes) > 0:
            xyxy_list = result.boxes.xyxy.cpu().tolist() if hasattr(result.boxes.xyxy, 'cpu') else result.boxes.xyxy.tolist()
            conf_list = result.boxes.conf.cpu().tolist() if hasattr(result.boxes.conf, 'cpu') else result.boxes.conf.tolist()
            cls_list = result.boxes.cls.cpu().tolist() if hasattr(result.boxes.cls, 'cpu') else result.boxes.cls.tolist()

            for xyxy, score, cls_idx in zip(xyxy_list, conf_list, cls_list):
                idx = int(cls_idx)
                detections.append({
                    "class_id": idx,
                    "class_name": str(names.get(idx, idx)),
                    "confidence": round(float(score), 4),
                    "box_xyxy": [round(float(v), 2) for v in xyxy],
                })

        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        annotated_name = f"signature_detect_{stamp}_{uuid.uuid4().hex[:8]}.png"
        annotated_path = LEGAL_OUTPUT_DIR / annotated_name
        
        try:
            plotted_bgr = result.plot()
            plotted_rgb = plotted_bgr[:, :, ::-1]
            from PIL import Image as PILImage
            PILImage.fromarray(plotted_rgb).save(annotated_path)
            annotated_url = f"/generated/legal/{annotated_name}"
        except Exception:
            annotated_url = None

        return jsonify({
            "model": model_path.name if model_path else "unknown",
            "count": len(detections),
            "detections": detections,
            "annotated_image_url": annotated_url,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ========================
# SRS API ENDPOINTS
# ========================

@app.route("/api/srs/health", methods=["GET"])
def srs_health():
    return jsonify({
        "status": "success",
        "message": "SRS backend is running.",
        "modules": [
            "SRS Evaluation",
            "Model-aware Evaluation",
            "DistilBERT FR/NFR outputs",
            "RoBERTa NFR subtype outputs",
            "RoBERTa ambiguity outputs",
            "RoBERTa quality outputs",
            "ResNet/CV page outputs",
            "Uploaded image/PDF page classification",
            "LIME / Grad-CAM XAI summaries",
            "SRS Generation",
            "RAG references",
            "DOCX/Markdown/ZIP export"
        ]
    })


@app.route("/api/srs/evaluate", methods=["POST"])
def srs_evaluate():
    try:
        text = ""
        uploaded_file_path = None
        uploaded_filename = None

        if "file" in request.files:
            uploaded_file = request.files["file"]
            uploaded_filename = os.path.basename(uploaded_file.filename or "uploaded_srs_file")
            temp_dir = tempfile.mkdtemp()
            uploaded_file_path = os.path.join(temp_dir, uploaded_filename)
            uploaded_file.save(uploaded_file_path)
            text = extract_text_from_file(uploaded_file_path)

        if not text:
            data = request.get_json(silent=True) or {}
            text = data.get("text", "")

        uploaded_ext = os.path.splitext(uploaded_file_path or "")[1].lower()
        is_visual_upload = uploaded_ext in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}

        if not text or len(text.strip()) < 20:
            if not is_visual_upload:
                return jsonify({
                    "status": "error",
                    "message": "No valid SRS text found. Please upload a PDF/TXT/MD/image file or paste SRS content."
                }), 400

            text = f"Visual SRS page uploaded: {uploaded_filename or 'uploaded image'}. OCR text was limited."

        result = evaluate_srs_with_models(text)
        result["input_text"] = text

        if is_visual_upload and len(text.strip()) < 90:
            result["ocr_warning"] = (
                "OCR extracted limited text from this visual upload; "
                "the ResNet/CV classification is more reliable than the textual SRS quality score for this file."
            )

        if uploaded_file_path:
            uploaded_visual = classify_uploaded_srs_visual(
                uploaded_file_path,
                extracted_text=text,
                original_filename=uploaded_filename or os.path.basename(uploaded_file_path),
            )

            if uploaded_visual:
                result["uploaded_visual_classification"] = uploaded_visual
                result.setdefault("model_based_evaluation", {})["uploaded_vision"] = uploaded_visual

                # Re-save report after adding uploaded image/PDF classification.
                result["report_files"] = save_evaluation_report(result)

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/api/srs/rewrite", methods=["POST"])
def srs_rewrite_requirements():
    try:
        import re
        import traceback

        data = request.get_json(silent=True) or {}
        text = data.get("text", "")

        if not text or len(text.strip()) < 20:
            return jsonify({
                "status": "error",
                "message": "No valid SRS text received for rewriting."
            }), 400

        def clean_line(value):
            value = str(value or "")
            value = value.replace("\u200b", " ")
            value = value.replace("\ufeff", " ")
            value = value.replace("●", " ")
            value = value.replace("○", " ")
            value = value.replace("•", " ")
            value = re.sub(r"^\s*[\-\*\d\.\)\(]+", "", value)
            value = re.sub(r"\s+", " ", value)
            value = value.strip(" -:\t\r\n.")
            return value

        def is_fragment(line):
            if not line:
                return True

            words = line.split()
            lower = line.lower()

            if len(words) < 4:
                return True

            # Bad OCR continuation fragments.
            if re.match(r"^[a-z]", line) and not any(
                key in lower
                for key in [
                    "users can",
                    "users must",
                    "the system",
                    "the platform",
                    "must",
                    "shall",
                    "should",
                    "can",
                ]
            ):
                return True

            # Half sentence ending with weak continuation.
            if lower.endswith(("will be", "and", "or", "for", "to", "with")):
                return True

            return False

        def extract_candidates(raw_text):
            normalized = raw_text.replace("\u200b", " ")
            raw_parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", normalized)

            candidates = []

            for part in raw_parts:
                line = clean_line(part)
                if not line:
                    continue

                # If OCR gives: "pushed. Users can modify..."
                # keep only the useful actor phrase.
                actor_match = re.search(
                    r"(Users?\s+(?:can|must|should|shall)\s+.+|The\s+(?:system|platform|application)\s+(?:must|should|shall|will)\s+.+)",
                    line,
                    flags=re.IGNORECASE,
                )
                if actor_match:
                    line = clean_line(actor_match.group(1))

                # Keep feature title with parenthesized behavior.
                if re.search(r"\(.+users?\s+(can|must|should|shall).+\)", line, flags=re.IGNORECASE):
                    candidates.append(line)
                    continue

                lower = line.lower()
                useful = any(key in lower for key in [
                    "users can",
                    "users must",
                    "users should",
                    "the system shall",
                    "the system must",
                    "the system should",
                    "the platform shall",
                    "the platform must",
                    "the platform should",
                    "downtime",
                    "response time",
                    "scalable",
                    "security",
                    "preferences",
                    "report posts",
                    "feedback",
                    "delete their accounts",
                    "search posts",
                ])

                if useful and not is_fragment(line):
                    candidates.append(line)

            # Deduplicate.
            unique = []
            seen = set()

            for item in candidates:
                key = item.lower().strip()
                if key not in seen:
                    seen.add(key)
                    unique.append(item)

            return unique[:15]

        def rewrite_requirement(original):
            original = clean_line(original)
            lower = original.lower()
            reason = []

            # Pattern: Report System (Users can report posts)
            feature_match = re.match(
                r"^(.*?)\s*\((Users?\s+(?:can|must|should|shall)\s+.+?)\)$",
                original,
                flags=re.IGNORECASE,
            )

            if feature_match:
                feature = clean_line(feature_match.group(1))
                behavior = clean_line(feature_match.group(2))

                action = re.sub(
                    r"^users?\s+(can|must|should|shall)\s+",
                    "",
                    behavior,
                    flags=re.IGNORECASE,
                )

                rewritten = f"The system shall allow users to {action} through the {feature}."
                reason.append("Converted feature label and user action into a complete functional requirement.")

                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": " ".join(reason),
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Users can update preferences.
            user_can = re.match(r"^users?\s+can\s+(.+)$", original, flags=re.IGNORECASE)
            if user_can:
                action = clean_line(user_can.group(1))
                rewritten = f"The system shall allow users to {action}."
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Converted informal user capability into a clear system requirement.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Users must sign up.
            user_must = re.match(r"^users?\s+must\s+(.+)$", original, flags=re.IGNORECASE)
            if user_must:
                action = clean_line(user_must.group(1))
                rewritten = f"The system shall require users to {action}."
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Converted user obligation into a testable system requirement.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Platform must not allow content outside preferences.
            if "not allow content outside of user preferences" in lower:
                rewritten = (
                    "The platform shall prevent content that does not match the user's configured preferences "
                    "from appearing in the user's content feed."
                )
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Clarified the preference-filtering rule and expressed it as enforceable platform behavior.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Search posts.
            if "search" in lower and "posts" in lower:
                rewritten = (
                    "The system shall allow users to search posts by title, body content, and relevant metadata."
                )
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Completed the incomplete search requirement and made the searchable fields explicit.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Scalability.
            if "scalable" in lower or "high traffic" in lower:
                rewritten = (
                    "The system shall support high traffic by defining measurable limits for concurrent users, "
                    "request throughput, response time, and resource utilization."
                )
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Rewrote vague scalability wording into measurable non-functional criteria.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Downtime.
            if "downtime" in lower:
                rewritten = (
                    "The system shall limit unplanned downtime to the maximum duration defined in the availability "
                    "acceptance criteria for the applicable reporting period."
                )
                return {
                    "original": original,
                    "rewritten": rewritten,
                    "reason": "Converted downtime wording into a measurable availability requirement.",
                    "source": "current_uploaded_document_smart_rewrite",
                }

            # Generic cleanup only if it already has a real actor.
            rewritten = original
            rewritten = re.sub(r"\bshould\b", "shall", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bmust\b", "shall", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bwill\b", "shall", rewritten, flags=re.IGNORECASE)

            vague_replacements = {
                "easy": "requiring no more than the defined number of user steps",
                "quickly": "within the defined maximum response time",
                "fast": "within the defined maximum response time",
                "user-friendly": "with clear navigation, accessible UI components, and validation messages",
                "efficient": "within defined processing-time and resource-usage limits",
                "secure": "using authentication, authorization, encrypted communication, and audit logging",
                "robust": "with validation, exception handling, recovery, and monitoring mechanisms",
            }

            for vague, precise in vague_replacements.items():
                rewritten = re.sub(
                    rf"\b{re.escape(vague)}\b",
                    precise,
                    rewritten,
                    flags=re.IGNORECASE,
                )

            if rewritten.lower().startswith("the system shall") or rewritten.lower().startswith("the platform shall"):
                pass
            elif rewritten.lower().startswith("the system "):
                rewritten = re.sub(r"^the system\s+", "The system shall ", rewritten, flags=re.IGNORECASE)
            elif rewritten.lower().startswith("the platform "):
                rewritten = re.sub(r"^the platform\s+", "The platform shall ", rewritten, flags=re.IGNORECASE)
            else:
                rewritten = f"The system shall {rewritten[0].lower() + rewritten[1:]}"

            rewritten = re.sub(r"\s+", " ", rewritten).strip()
            rewritten = rewritten.replace("The system shall The system", "The system")
            rewritten = rewritten.replace("The platform shall The platform", "The platform")
            rewritten = rewritten.rstrip(".") + "."

            return {
                "original": original,
                "rewritten": rewritten,
                "reason": "Normalized the requirement and replaced weak or vague wording where possible.",
                "source": "current_uploaded_document_smart_rewrite",
            }

        candidates = extract_candidates(text)

        if not candidates:
            return jsonify({
                "status": "success",
                "message": "No clear weak requirements were found in the uploaded document.",
                "rewrite_count": 0,
                "rewrites": []
            })

        rewrites = [rewrite_requirement(item) for item in candidates]

        return jsonify({
            "status": "success",
            "message": "Requirement rewriting completed using the currently uploaded document.",
            "rewrite_count": len(rewrites),
            "rewrites": rewrites,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/api/srs/generate", methods=["POST"])
def srs_generate():
    try:
        data = request.get_json(silent=True) or {}

        result = generate_srs_document(data)
        result["xai"] = get_generation_xai_summary()

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/srs/download", methods=["GET"])
def srs_download():
    file_path = request.args.get("file")

    if not file_path or not os.path.exists(file_path):
        return jsonify({
            "status": "error",
            "message": "File not found."
        }), 404

    return send_file(file_path, as_attachment=True)


@app.route("/api/srs/download-report", methods=["GET"])
def srs_download_report():
    file_path = request.args.get("file")

    if not file_path or not os.path.exists(file_path):
        return jsonify({
            "status": "error",
            "message": "Report file not found."
        }), 404

    return send_file(file_path, as_attachment=True)



if __name__ == '__main__':
    # Load models on startup
    load_models()

    #BMC MODELS INITIALIZATION
    init_document_classifier()

    init_bmc_processor()

    init_bmc_eval()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
