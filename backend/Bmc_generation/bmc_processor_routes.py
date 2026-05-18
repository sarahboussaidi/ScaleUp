"""
BMC Processor Routes

Correct pipeline:
1. Document classifier detects if image is BMC.
2. If BMC:
   - YOLO detects BMC visual blocks.
   - Each detected block is cropped.
   - OCR extracts text from each crop.
   - DistilBERT classifies extracted text/chunks into BMC blocks.
3. If YOLO detects 0 blocks:
   - Template layout crops the standard BMC regions.
   - OCR extracts text from each region.
   - DistilBERT classifies extracted text/chunks.
4. If not BMC:
   - Page-level OCR.
   - DistilBERT classifies extracted text/chunks.
5. Optional LLM completion with Qwen.
"""

import io
import os
import re
import json
import logging
import traceback

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from flask import Blueprint, request, jsonify
import requests
import faiss
from sentence_transformers import SentenceTransformer

from Bmc_generation.document_classifier_routes import (
    preprocess_image as doc_preprocess_image,
    predict_document_type as doc_predict_document_type,
)

bmc_processor_bp = Blueprint("bmc_processor", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

BMC_BLOCKS = [
    "key_partnerships",
    "key_activities",
    "key_resources",
    "value_proposition",
    "customer_relationships",
    "channels",
    "customer_segments",
    "cost_structure",
    "revenue_streams",
    "other",
]

SDG_NAMES = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals",
}

TEXT_CLASSIFIER_PATH = os.path.join(PROJECT_ROOT, "models", "bmc_generation", "text_classifier")
YOLO_WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "models", "bmc_generation", "yolo_s.pt")
SDG_CLASSIFIER_PATH = os.path.join(PROJECT_ROOT, "models", "bmc_generation", "sdg_distilbert")
RAG_INDEX_PATH = os.path.join(BASE_DIR, "rag_index")
EMBEDDING_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "bmc_generation", "embedding_model")

_ocr_reader = None
_yolo_model = None
_trocr_processor = None
_trocr_model = None
_text_classifier_model = None
_text_classifier_tokenizer = None
_llm_tokenizer = None
_llm_model = None
_sdg_classifier_model = None
_sdg_classifier_tokenizer = None
_rag_index = None
_rag_chunks = None
_rag_embedder = None

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")

if not HF_TOKEN:
    # Keep backend logs clean when running with public models and no HF auth.
    logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)


def hf_auth_kwargs():
    return {"token": HF_TOKEN} if HF_TOKEN else {}


# If the token is present in the environment, also ensure the huggingface_hub
# library sees it by setting the canonical env var and attempting a login.
if HF_TOKEN:
    try:
        os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", HF_TOKEN)
        # Attempt a safe login (no-op if huggingface_hub not installed)
        try:
            from huggingface_hub import login as _hf_login
            _hf_login(token=HF_TOKEN)
        except Exception:
            # If login fails, continue — the env var should be sufficient
            pass

        masked = HF_TOKEN[:6] + "..." + HF_TOKEN[-4:] if len(HF_TOKEN) > 12 else "(provided)"
        print(f"[HF] HF token detected and exported to HUGGINGFACE_HUB_TOKEN (masked={masked})")
    except Exception as e:
        print(f"[HF] Failed to propagate HF token: {e}")


# ==================== BASIC HELPERS ====================

def empty_bmc():
    return {block: [] for block in BMC_BLOCKS}


def normalize_label(label):
    return str(label).strip().lower().replace("-", "_").replace(" ", "_")


def _make_filelike(bytes_data, filename):
    bio = io.BytesIO(bytes_data)
    bio.filename = filename
    bio.seek(0)
    return bio


def clean_ocr_text(text):
    if text is None:
        return ""
    text = str(text).replace("\r", " ").replace("\t", " ")
    text = text.replace("|", "I")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_noise_text(text):
    if not text:
        return True

    t = clean_ocr_text(text).lower()

    if len(t) < 3:
        return True

    noise_patterns = [
        "business model canvas",
        "the business model analyst",
        "businessmodelanalyst",
        "businessmodelanalystcom",
        "businessmodelanalyst.com",
        "key partners",
        "keys partners",
        "key activities",
        "key resources",
        "value propositions",
        "value proposition",
        "customer relationship",
        "customer relationships",
        "customer segments",
        "cost structure",
        "revenue streams",
        "channels",
    ]

    return any(pattern in t for pattern in noise_patterns)


def split_into_sentences(text):
    if not text:
        return []

    text = text.replace("\r", "\n")
    chunks = re.split(r"[\n•]+|(?<=[.!?])\s+", text)
    chunks = [clean_ocr_text(chunk) for chunk in chunks if clean_ocr_text(chunk)]

    return [chunk for chunk in chunks if len(chunk) >= 3 and not is_noise_text(chunk)]


def split_into_chunks(text, max_words=20):
    if not text:
        return []

    sentences = split_into_sentences(text)
    final_chunks = []

    for sentence in sentences:
        words = sentence.split()

        if len(words) <= max_words:
            final_chunks.append(sentence)
        else:
            for i in range(0, len(words), max_words):
                chunk = " ".join(words[i:i + max_words]).strip()
                if chunk and not is_noise_text(chunk):
                    final_chunks.append(chunk)

    return final_chunks


# ==================== LOADERS ====================

def load_ocr_reader():
    global _ocr_reader

    if _ocr_reader is not None:
        return _ocr_reader

    try:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available())
        return _ocr_reader
    except Exception as e:
        print(f"⚠️ EasyOCR not available: {e}")
        traceback.print_exc()
        return None


def load_yolo_model():
    global _yolo_model

    if _yolo_model is not None:
        return _yolo_model

    try:
        from ultralytics import YOLO

        print(f"[YOLO] Loading weights from: {YOLO_WEIGHTS_PATH}")

        if not os.path.exists(YOLO_WEIGHTS_PATH):
            print("[YOLO] Weights not found. Expected: models\\bmc_generation\\yolo_s.pt")
            return None

        model = YOLO(YOLO_WEIGHTS_PATH)
        print("[YOLO] Classes:", model.names)

        classes_text = str(model.names).lower()
        coco_words = ["person", "car", "dog", "cat", "bicycle", "truck", "bus"]

        if any(word in classes_text for word in coco_words):
            raise ValueError("Wrong YOLO model: COCO classes detected. Use BMC YOLO weights.")

        _yolo_model = model
        return _yolo_model

    except Exception as e:
        print(f"⚠️ YOLO loading failed: {e}")
        traceback.print_exc()
        return None


def load_trocr_model():
    global _trocr_processor, _trocr_model

    if _trocr_processor is not None and _trocr_model is not None:
        return _trocr_processor, _trocr_model

    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        local_dir = os.path.join(BASE_DIR, "models", "trocr-base-handwritten")

        if os.path.isdir(local_dir):
            processor = TrOCRProcessor.from_pretrained(local_dir, local_files_only=True)
            model = VisionEncoderDecoderModel.from_pretrained(local_dir, local_files_only=True)
        else:
            processor = TrOCRProcessor.from_pretrained(
                "microsoft/trocr-base-handwritten",
                **hf_auth_kwargs(),
            )
            model = VisionEncoderDecoderModel.from_pretrained(
                "microsoft/trocr-base-handwritten",
                **hf_auth_kwargs(),
            )

        model.to(DEVICE)
        model.eval()

        _trocr_processor = processor
        _trocr_model = model

        return processor, model

    except Exception as e:
        print(f"⚠️ TrOCR not available: {e}")
        traceback.print_exc()
        return None, None


def load_text_classifier():
    global _text_classifier_model, _text_classifier_tokenizer

    if _text_classifier_model is not None and _text_classifier_tokenizer is not None:
        return _text_classifier_model, _text_classifier_tokenizer

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        tokenizer = AutoTokenizer.from_pretrained(TEXT_CLASSIFIER_PATH, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            TEXT_CLASSIFIER_PATH,
            local_files_only=True,
        )

        model.to(DEVICE)
        model.eval()

        _text_classifier_model = model
        _text_classifier_tokenizer = tokenizer

        print("[TEXT-CLASSIFIER] Loaded successfully")
        print("[TEXT-CLASSIFIER] Labels:", model.config.id2label)

        return model, tokenizer

    except Exception as e:
        print(f"⚠️ Text classifier not available: {e}")
        traceback.print_exc()
        return None, None


def load_sdg_classifier():
    global _sdg_classifier_model, _sdg_classifier_tokenizer

    if _sdg_classifier_model is not None and _sdg_classifier_tokenizer is not None:
        return _sdg_classifier_model, _sdg_classifier_tokenizer

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        tokenizer = AutoTokenizer.from_pretrained(SDG_CLASSIFIER_PATH, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            SDG_CLASSIFIER_PATH,
            local_files_only=True,
        )

        model.to(DEVICE)
        model.eval()

        _sdg_classifier_model = model
        _sdg_classifier_tokenizer = tokenizer

        print("[SDG] Model loaded")
        print("[SDG] Labels:", model.config.id2label)

        return model, tokenizer

    except Exception as e:
        print(f"[SDG] Model load failed: {e}")
        traceback.print_exc()
        return None, None


def load_rag_index():
    global _rag_index, _rag_chunks, _rag_embedder

    if _rag_index is not None and _rag_chunks is not None and _rag_embedder is not None:
        return _rag_index, _rag_chunks, _rag_embedder

    try:
        index_path = os.path.join(RAG_INDEX_PATH, "sustainability_faiss.index")
        chunks_path = os.path.join(RAG_INDEX_PATH, "chunks_metadata.json")

        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            print(f"[RAG] Index files missing in: {RAG_INDEX_PATH}")
            return None, [], None

        _rag_index = faiss.read_index(index_path)
        with open(chunks_path, "r", encoding="utf-8") as f:
            _rag_chunks = json.load(f)

        _rag_embedder = SentenceTransformer(EMBEDDING_MODEL_PATH)

        print(f"[RAG] Loaded chunks: {len(_rag_chunks)}")
        return _rag_index, _rag_chunks, _rag_embedder

    except Exception as e:
        print(f"[RAG] Load failed: {e}")
        traceback.print_exc()
        return None, [], None


def bmc_to_text(bmc_json):
    parts = []
    for block in BMC_BLOCKS:
        for item in bmc_json.get(block, []) or []:
            if isinstance(item, dict):
                text = item.get("text", "")
            else:
                text = str(item)
            text = clean_ocr_text(text)
            if text:
                parts.append(text)

    return "\n".join(parts)


def predict_sdgs_from_bmc(bmc_json):
    try:
        model, tokenizer = load_sdg_classifier()
        if model is None or tokenizer is None:
            return []

        text = bmc_to_text(bmc_json)
        if not text:
            return []

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=1).squeeze(0)

        k = min(3, probs.numel())
        top_vals, top_idxs = torch.topk(probs, k=k)

        id2label = getattr(model.config, "id2label", {}) or {}
        predictions = []
        for score, idx in zip(top_vals.tolist(), top_idxs.tolist()):
            label = id2label.get(int(idx), "")
            sdg_num = None
            if label.startswith("LABEL_"):
                try:
                    sdg_num = int(label.replace("LABEL_", "")) + 1
                except ValueError:
                    sdg_num = None
            if sdg_num is None:
                sdg_num = int(idx) + 1

            sdg_name = SDG_NAMES.get(sdg_num, f"SDG {sdg_num}")
            label = f"SDG {sdg_num}: {sdg_name}"
            predictions.append({
                "sdg": label,
                "confidence": round(float(score), 4),
            })

        print(f"[SDG] Predictions: {predictions}")
        return predictions

    except Exception as e:
        print(f"[SDG] Prediction failed: {e}")
        traceback.print_exc()
        return []


def retrieve_sustainability_context(query, top_k=4):
    try:
        if not query:
            return []

        index, chunks, embedder = load_rag_index()
        if index is None or embedder is None or not chunks:
            return []

        query_embedding = embedder.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = index.search(query_embedding, top_k)
        results = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            chunk = chunks[idx] if idx < len(chunks) else {}
            results.append({
                "source": chunk.get("source", "unknown"),
                "chunk_id": chunk.get("chunk_id", int(idx)),
                "text": chunk.get("text", ""),
                "distance": float(dist),
            })

        print(f"[RAG] Retrieved top_k: {len(results)}")
        return results

    except Exception as e:
        print(f"[RAG] Retrieval failed: {e}")
        traceback.print_exc()
        return []


def load_llm_model(model_name="Qwen/Qwen2.5-1.5B-Instruct"):
    global _llm_tokenizer, _llm_model

    if _llm_tokenizer is not None and _llm_model is not None:
        return _llm_tokenizer, _llm_model

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM

        dtype = torch.float16 if DEVICE == "cuda" else torch.float32

        tokenizer = AutoTokenizer.from_pretrained(model_name, **hf_auth_kwargs())
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            **hf_auth_kwargs(),
        )

        model.to(DEVICE)
        model.eval()

        _llm_tokenizer = tokenizer
        _llm_model = model

        return tokenizer, model

    except Exception as e:
        print(f"⚠️ LLM loading failed: {e}")
        traceback.print_exc()
        return None, None


# ==================== OCR ====================

def extract_text_easyocr(image_array, filename="image"):
    reader = load_ocr_reader()

    if reader is None:
        raise RuntimeError("EasyOCR reader not available")

    print(f"[EasyOCR] {filename} shape={image_array.shape}")
    results = reader.readtext(image_array, detail=0, paragraph=True)
    text = "\n".join(results).strip()

    print(f"[EasyOCR] Extracted {len(results)} lines")
    return text


def _deskew_image(gray):
    try:
        import cv2

        # Threshold to get foreground
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh < 255))
        if coords.size == 0:
            return gray

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        print(f"[OCR-PRE] Deskew angle={angle:.2f}")
        return rotated
    except Exception as e:
        print(f"[OCR-PRE] Deskew failed: {e}")
        return gray


def _clean_ocr_lines(lines):
    cleaned = []
    for line in lines:
        t = clean_ocr_text(line)
        t = t.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("—", "-")
        t = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", t)
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)  # merge hyphen line breaks
        t = re.sub(r"\s{2,}", " ", t).strip()
        if len(t) < 2:
            continue
        cleaned.append(t)

    return cleaned


def _ocr_text_quality(text):
    """
    Heuristic to detect garbage OCR output (e.g., repeated letters).
    Returns a tuple: (is_usable, reason).
    """
    t = clean_ocr_text(text)
    if not t:
        return False, "empty"

    # Require a minimum amount of alphanumeric content
    alnum = re.sub(r"[^A-Za-z0-9]", "", t)
    if len(alnum) < 8:
        return False, "too_short"

    # Reject if one character dominates (e.g., WWWWWW)
    counts = {}
    for ch in alnum.lower():
        counts[ch] = counts.get(ch, 0) + 1
    max_ratio = max(counts.values()) / max(1, len(alnum))
    if max_ratio > 0.55:
        return False, "dominant_char"

    return True, "ok"


def extract_text_easyocr_typed(image_array, filename="image"):
    reader = load_ocr_reader()

    if reader is None:
        raise RuntimeError("EasyOCR reader not available")

    print(f"[EasyOCR-TYPED] {filename} shape={image_array.shape}")
    results = reader.readtext(
        image_array,
        detail=1,
        paragraph=False,
        decoder="beamsearch",
        beamWidth=5,
        contrast_ths=0.2,
        adjust_contrast=0.7,
        text_threshold=0.6,
        low_text=0.4,
        link_threshold=0.4,
        width_ths=0.7,
    )

    kept = []
    confidences = []
    for (_bbox, text, conf) in results:
        if conf is None:
            continue
        if conf < 0.35:
            continue
        kept.append(text)
        confidences.append(conf)

    avg_conf = float(np.mean(confidences)) if confidences else 0.0
    print(f"[EasyOCR-TYPED] Raw lines={len(results)}, kept={len(kept)}, avg_conf={avg_conf:.3f}")

    cleaned_lines = _clean_ocr_lines(kept)
    preview = " | ".join(cleaned_lines[:3])
    print(f"[EasyOCR-TYPED] Cleaned preview: {preview}")

    return "\n".join(cleaned_lines).strip()


def preprocess_for_ocr(image_pil, mode="auto"):
    """
    Preprocess PIL image for OCR. For `typed` documents we apply
    resizing, denoising and adaptive thresholding to improve OCR on
    scanned/printed pages.
    """
    try:
        import cv2

        img = np.array(image_pil.convert("RGB"))

        if mode == "typed":
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            # Upscale to improve OCR on low-resolution scans
            h, w = gray.shape[:2]
            target_w = 1600
            if w > 0 and w < target_w:
                scale = target_w / float(w)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (target_w, new_h), interpolation=cv2.INTER_CUBIC)

            # Denoise
            gray = cv2.fastNlMeansDenoising(gray, h=18, templateWindowSize=7, searchWindowSize=21)

            # CLAHE contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

            # Deskew
            gray = _deskew_image(gray)

            # Sharpen text
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            gray = cv2.filter2D(gray, -1, kernel)

            # Adaptive threshold to handle uneven lighting
            try:
                thr = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
                )
                return thr
            except Exception:
                return gray

        # default: return RGB numpy array
        return np.array(image_pil.convert("RGB"))

    except Exception as e:
        # If OpenCV not available, fallback to plain image
        print(f"[OCR-PRE] cv2 preprocessing failed or not installed: {e}")
        return np.array(image_pil.convert("RGB"))


def extract_text_trocr(image_pil, filename="image"):
    processor, model = load_trocr_model()

    if processor is None or model is None:
        print("[TrOCR] Falling back to EasyOCR")
        return extract_text_easyocr(np.array(image_pil), filename)

    try:
        pixel_values = processor(
            images=image_pil.convert("RGB"),
            return_tensors="pt",
        ).pixel_values.to(DEVICE)

        with torch.no_grad():
            generated_ids = model.generate(pixel_values, max_length=128)

        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return clean_ocr_text(text)

    except Exception as e:
        print(f"⚠️ TrOCR failed, fallback EasyOCR: {e}")
        traceback.print_exc()
        return extract_text_easyocr(np.array(image_pil), filename)




def extract_text_from_image(image_file, ocr_method="easyocr", doc_type=None):
    """
    Extract text and accept a `doc_type` hint (e.g., 'typed') to
    improve preprocessing. Returns cleaned text string.
    """
    image_data = image_file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    # Prefer TrOCR printed when doc_type indicates typed/printed document
    if doc_type == "typed":
        # try printed TrOCR first
        try:
            # attempt to load a printed TrOCR variant dynamically
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            try:
                local_dir = os.path.join(BASE_DIR, "models", "trocr-base-printed")
                if os.path.isdir(local_dir):
                    processor = TrOCRProcessor.from_pretrained(local_dir, local_files_only=True)
                    model = VisionEncoderDecoderModel.from_pretrained(local_dir, local_files_only=True)
                else:
                    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed", **hf_auth_kwargs())
                    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed", **hf_auth_kwargs())

                model.to(DEVICE)
                model.eval()

                pixel_values = processor(images=image.convert("RGB"), return_tensors="pt").pixel_values.to(DEVICE)
                with torch.no_grad():
                    generated_ids = model.generate(pixel_values, max_length=512)
                text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                cleaned = clean_ocr_text(text)
                ok, reason = _ocr_text_quality(cleaned)
                print(f"[TrOCR-printed] quality={reason} len={len(cleaned)}")
                if ok:
                    return cleaned
                # fall through to EasyOCR typed
            except Exception as e:
                print(f"[TrOCR-printed] Failed to run printed TrOCR: {e}")
                # fall through to EasyOCR with typed preprocessing
        except Exception as e:
            print(f"[TrOCR-printed] Transformers not available or failed: {e}")

        # Preprocess for typed document then run EasyOCR
        pre_arr = preprocess_for_ocr(image, mode="typed")
        return extract_text_easyocr_typed(pre_arr, getattr(image_file, "filename", "image"))

    # For trocr request explicitly
    if ocr_method == "trocr":
        return extract_text_trocr(image, getattr(image_file, "filename", "image"))

    # Default: use EasyOCR with light preprocessing
    pre_arr = preprocess_for_ocr(image, mode="auto")
    return extract_text_easyocr(pre_arr, getattr(image_file, "filename", "image"))


# ==================== YOLO ====================

def detect_bmc_blocks(pil_image, conf_threshold=0.05):
    model = load_yolo_model()

    if model is None:
        print("[YOLO] No model available")
        return []

    image_np = np.array(pil_image.convert("RGB"))
    h, w = image_np.shape[:2]

    print(f"[YOLO] Image size: {w}x{h}")
    print(f"[YOLO] Running detection with conf={conf_threshold}, imgsz=1024")

    try:
        results = model(image_np, conf=conf_threshold, imgsz=1024, verbose=False)
    except Exception as e:
        print(f"⚠️ YOLO inference failed: {e}")
        traceback.print_exc()
        return []

    detections = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            conf = float(box.conf[0].cpu().numpy())
            cls_idx = int(box.cls[0].cpu().numpy())

            class_name = model.names.get(cls_idx, f"unknown_{cls_idx}")
            normalized_class = normalize_label(class_name)

            det = {
                "xyxy": tuple(map(int, xyxy)),
                "conf": conf,
                "cls": cls_idx,
                "class_name": class_name,
                "normalized_class": normalized_class,
            }

            detections.append(det)

            print(
                f"[YOLO] Detected class='{class_name}' "
                f"conf={conf:.3f} box={det['xyxy']}"
            )

    detections = sorted(detections, key=lambda d: (d["xyxy"][1], d["xyxy"][0]))
    print(f"[YOLO] Total detections: {len(detections)}")

    return detections


# ==================== DISTILBERT CLASSIFICATION ====================
def classify_bmc_chunk(
    text,
    tokenizer,
    model,
    confidence_threshold=0.50,
    visual_block_hint=None,
    require_confidence_without_hint=True,
):
    text = clean_ocr_text(text)

    if not text or is_noise_text(text):
        return None

    label_mapping = {
        "key_partners": "key_partnerships",
        "key_partnerships": "key_partnerships",
        "key_activities": "key_activities",
        "key_resources": "key_resources",
        "value_proposition": "value_proposition",
        "value_propositions": "value_proposition",
        "customer_relationship": "customer_relationships",
        "customer_relationships": "customer_relationships",
        "channels": "channels",
        "channel": "channels",
        "customer_segments": "customer_segments",
        "customer_segment": "customer_segments",
        "cost_structure": "cost_structure",
        "cost_structures": "cost_structure",
        "revenue_streams": "revenue_streams",
        "revenue_stream": "revenue_streams",
        "other": "other",
    }

    hint = None
    if visual_block_hint:
        hint = normalize_label(visual_block_hint)
        hint = label_mapping.get(hint, hint)
        if hint not in BMC_BLOCKS:
            hint = None

    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )

        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)[0]
            pred_idx = torch.argmax(probs).item()
            confidence = probs[pred_idx].item()

        raw_label = model.config.id2label.get(pred_idx, "other")
        raw_block = normalize_label(raw_label)
        raw_block = label_mapping.get(raw_block, raw_block)

        if raw_block not in BMC_BLOCKS:
            raw_block = "other"

        # IMPORTANT:
        # If the text comes from a YOLO/template crop, the visual hint wins.
        if hint:
            final_block = hint
            source = "visual_hint_plus_distilbert"
        else:
            if confidence < confidence_threshold and require_confidence_without_hint:
                final_block = "other"
                source = "distilbert_low_confidence"
            else:
                final_block = raw_block
                source = "distilbert_classifier"

        print(
            f"[DistilBERT] '{text[:70]}' -> raw={raw_block} "
            f"final={final_block} conf={confidence:.2%} hint={hint}"
        )

        return {
            "text": text,
            "block": final_block,
            "confidence": float(confidence),
            "source": source,
            "raw_block": raw_block,
            "visual_hint": hint,
        }

    except Exception as e:
        print(f"⚠️ Classification failed for '{text[:50]}': {e}")
        traceback.print_exc()

        return {
            "text": text,
            "block": hint if hint else "other",
            "confidence": 0.0,
            "source": "error_visual_hint" if hint else "distilbert_error",
            "raw_block": "other",
            "visual_hint": hint,
        }
def classify_texts_with_distilbert(
    texts,
    confidence_threshold=0.50,
    visual_block_hint=None,
    require_confidence_without_hint=True,
):
    model, tokenizer = load_text_classifier()

    if model is None or tokenizer is None:
        print("⚠️ Text classifier missing")
        return []

    results = []

    for text in texts:
        chunks = split_into_chunks(text, max_words=20)

        for chunk in chunks:
            item = classify_bmc_chunk(
                chunk,
                tokenizer,
                model,
                confidence_threshold=confidence_threshold,
                visual_block_hint=visual_block_hint,
                require_confidence_without_hint=require_confidence_without_hint,
            )

            if item is not None:
                results.append(item)

    return results

def build_bmc_from_classifications(classifications):
    bmc = empty_bmc()

    for item in classifications:
        block = item.get("block", "other")

        if block not in BMC_BLOCKS:
            block = "other"

        text = item.get("text", "")

        if not text or is_noise_text(text):
            continue

        bmc[block].append({
            "text": text,
            "confidence": round(float(item.get("confidence", 0.0)), 4),
            "source": item.get("source", "distilbert_classifier"),
        })

    return bmc


# ==================== BMC-SPECIFIC PIPELINES ====================

def ocr_yolo_crops_then_classify(pil_image, detections, ocr_method="easyocr", confidence_threshold=0.50):
    classifications = []
    crop_debug = []
    all_chunks = []

    print("[PIPELINE] Using YOLO crop OCR + DistilBERT classification WITH visual hints")

    for i, det in enumerate(detections):
        try:
            x1, y1, x2, y2 = det["xyxy"]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(pil_image.width, x2), min(pil_image.height, y2)

            if x2 <= x1 or y2 <= y1:
                print(f"[YOLO-CROP] Skip invalid crop {i}")
                continue

            visual_hint = det.get("normalized_class")

            crop = pil_image.crop((x1, y1, x2, y2))

            if ocr_method == "trocr":
                text = extract_text_trocr(crop, f"yolo_crop_{i}")
            else:
                text = extract_text_easyocr(np.array(crop), f"yolo_crop_{i}")

            chunks = split_into_chunks(text, max_words=20)
            all_chunks.extend(chunks)

            crop_classifications = classify_texts_with_distilbert(
                chunks,
                confidence_threshold=confidence_threshold,
                visual_block_hint=visual_hint
            )

            classifications.extend(crop_classifications)

            crop_debug.append({
                "crop_index": i,
                "yolo_class": det.get("class_name", "unknown"),
                "visual_hint": visual_hint,
                "yolo_confidence": round(float(det.get("conf", 0.0)), 4),
                "ocr_text": text,
                "chunks": chunks,
                "classifications": crop_classifications,
            })

            print(f"[YOLO-CROP] Block {i} hint={visual_hint} chunks={chunks}")

        except Exception as e:
            print(f"⚠️ Error processing YOLO crop {i}: {e}")
            traceback.print_exc()

    bmc_json = build_bmc_from_classifications(classifications)
    extracted_text = "\n".join(all_chunks)

    return bmc_json, extracted_text, classifications, crop_debug

def crop_region(pil_image, rel_box):
    w, h = pil_image.size
    x1 = int(rel_box[0] * w)
    y1 = int(rel_box[1] * h)
    x2 = int(rel_box[2] * w)
    y2 = int(rel_box[3] * h)
    return pil_image.crop((x1, y1, x2, y2))


def template_crops_then_classify(pil_image, ocr_method="easyocr", confidence_threshold=0.50):
    print("[PIPELINE] Using template layout OCR + DistilBERT classification WITH visual hints")

    regions = {
        "key_partnerships": (0.00, 0.12, 0.20, 0.78),
        "key_activities": (0.20, 0.12, 0.40, 0.45),
        "key_resources": (0.20, 0.45, 0.40, 0.78),
        "value_proposition": (0.40, 0.12, 0.60, 0.78),
        "customer_relationships": (0.60, 0.12, 0.80, 0.45),
        "channels": (0.60, 0.45, 0.80, 0.78),
        "customer_segments": (0.80, 0.12, 1.00, 0.78),
        "cost_structure": (0.00, 0.78, 0.50, 1.00),
        "revenue_streams": (0.50, 0.78, 1.00, 1.00),
    }

    classifications = []
    crop_debug = []
    all_chunks = []

    for visual_hint, rel_box in regions.items():
        try:
            crop = crop_region(pil_image, rel_box)

            if ocr_method == "trocr":
                text = extract_text_trocr(crop, visual_hint)
            else:
                text = extract_text_easyocr(np.array(crop), visual_hint)

            chunks = split_into_chunks(text, max_words=20)
            all_chunks.extend(chunks)

            region_classifications = classify_texts_with_distilbert(
                chunks,
                confidence_threshold=confidence_threshold,
                visual_block_hint=visual_hint
            )

            classifications.extend(region_classifications)

            crop_debug.append({
                "region": visual_hint,
                "visual_hint": visual_hint,
                "ocr_text": text,
                "chunks": chunks,
                "classifications": region_classifications,
            })

            print(f"[TEMPLATE-CROP] {visual_hint}: {chunks}")

        except Exception as e:
            print(f"⚠️ Template crop failed for {visual_hint}: {e}")
            traceback.print_exc()

    bmc_json = build_bmc_from_classifications(classifications)
    extracted_text = "\n".join(all_chunks)

    return bmc_json, extracted_text, classifications, crop_debug
# ==================== LLM ====================

def simplify_bmc_json(bmc_json):
    simple = {}

    for block in BMC_BLOCKS:
        items = bmc_json.get(block, [])
        simple[block] = [
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in items
        ]

    return simple


def summarize_classifications(classifications):
    summary = {block: [] for block in BMC_BLOCKS}

    for item in classifications or []:
        block = item.get("block", "other")
        if block not in summary:
            block = "other"

        text = clean_ocr_text(item.get("text", ""))
        confidence = float(item.get("confidence", 0.0))

        if text:
            summary[block].append(f"- {text} (conf: {confidence:.2f})")

    return summary


def normalize_bmc_section_key(raw_heading):
    if not raw_heading:
        return None

    heading = clean_ocr_text(raw_heading).lower()
    heading = re.sub(r"^\d+\.?\s*", "", heading)
    heading = heading.replace("**", "").strip()

    aliases = {
        "key partnerships": "key_partnerships",
        "key partners": "key_partnerships",
        "key activities": "key_activities",
        "key resources": "key_resources",
        "value proposition": "value_proposition",
        "customer relationships": "customer_relationships",
        "channels": "channels",
        "customer segments": "customer_segments",
        "cost structure": "cost_structure",
        "revenue streams": "revenue_streams",
    }

    return aliases.get(heading)


def extract_llm_sections(llm_text):
    sections = {}
    current_key = None
    current_lines = []

    for raw_line in (llm_text or "").replace("\r", "").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        heading_match = re.match(r"^(?:#{1,6}\s*|\*\*)?(?:\d+\.?\s*)?(.+?)(?:\*\*)?$", line)
        if heading_match and (line.startswith("#") or line.startswith("**") or re.match(r"^\d+\.?\s*", line)):
            candidate_key = normalize_bmc_section_key(heading_match.group(1))
            if candidate_key:
                if current_key and current_lines:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = candidate_key
                current_lines = []
                continue

        if current_key:
            current_lines.append(line)

    if current_key and current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def build_fallback_section(block_key, simple_bmc, classification_summary):
    source_lines = []

    for entry in (simple_bmc.get(block_key, []) or [])[:3]:
        if entry:
            source_lines.append(f"- {entry}")

    if not source_lines:
        for entry in (classification_summary.get(block_key, []) or [])[:3]:
            if entry:
                source_lines.append(entry)

    if not source_lines:
        source_lines.append("- Not clearly visible")

    return "\n".join(source_lines)


def ensure_all_bmc_sections(llm_text, simple_bmc, classification_summary):
    section_order = [
        ("key_partnerships", "Key Partnerships"),
        ("key_activities", "Key Activities"),
        ("key_resources", "Key Resources"),
        ("value_proposition", "Value Proposition"),
        ("customer_relationships", "Customer Relationships"),
        ("channels", "Channels"),
        ("customer_segments", "Customer Segments"),
        ("cost_structure", "Cost Structure"),
        ("revenue_streams", "Revenue Streams"),
    ]

    parsed_sections = extract_llm_sections(llm_text)
    output_sections = []

    for block_key, label in section_order:
        content = parsed_sections.get(block_key, "").strip()
        if not content:
            content = build_fallback_section(block_key, simple_bmc, classification_summary)

        output_sections.append(f"### {label}\n{content}")

    return "\n\n".join(output_sections).strip()


def _parse_llm_section_items(section_text, max_items=4):
    items = []
    for raw_line in (section_text or "").replace("\r", "").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        line = clean_ocr_text(line)
        if line and line.lower() != "not clearly visible":
            items.append(line)

    # Keep stable order, remove duplicates.
    deduped = []
    seen = set()
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped[:max_items]


def backfill_bmc_with_llm_sections(bmc_json, llm_text):
    if not llm_text:
        return bmc_json

    parsed_sections = extract_llm_sections(llm_text)
    if not parsed_sections:
        return bmc_json

    merged = {block: list(bmc_json.get(block, []) or []) for block in BMC_BLOCKS}

    for block in BMC_BLOCKS:
        if block == "other":
            continue

        existing = merged.get(block, []) or []
        has_content = any(
            clean_ocr_text(item.get("text", "") if isinstance(item, dict) else str(item))
            for item in existing
        )
        if has_content:
            continue

        section_text = parsed_sections.get(block, "")
        items = _parse_llm_section_items(section_text)
        if not items:
            continue

        merged[block] = [
            {
                "text": item,
                "block": block,
                "label": "llm_backfill",
                "confidence": 0.0,
                "source": "llm",
            }
            for item in items
        ]

    return merged


def generate_bmc_with_llm(bmc_json, classifications=None, classification_mode=None):

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not found")

    simple_bmc = simplify_bmc_json(bmc_json)
    classification_summary = summarize_classifications(classifications)

    prompt = f"""
You are a Business Model Canvas expert.

Using the classifier output below, produce a short and clear Business Model Canvas.
Keep the output understandable, concise, and directly related to the classifier input.
Do not add long explanations, marketing language, or invented details.
If something is uncertain, keep it simple.
You must include all 9 BMC sections in the final answer.
You must keep the response short enough to fit on one screen.

Classifier mode:
{classification_mode or "unknown"}

Classifier evidence:
{json.dumps(classification_summary, indent=2, ensure_ascii=False)}

Current BMC blocks:
{json.dumps(simple_bmc, indent=2, ensure_ascii=False)}

Rules:
- Use the 9 official BMC blocks.
- Keep each block short and understandable.
- Use the classifier evidence as the main source.
- Do not develop the answer too much.
- Use short bullets or short phrases only.
- Include every block even if the evidence is limited.
- If a block is weak or missing, state a short simple fallback.
- Return exactly 9 sections with these headings in this order:
    Key Partnerships, Key Activities, Key Resources, Value Proposition, Customer Relationships, Channels, Customer Segments, Cost Structure, Revenue Streams.
"""
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful Business Model Canvas expert."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 700,
        },
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Groq error {response.status_code}: {response.text}")

    data = response.json()
    llm_text = data["choices"][0]["message"]["content"]

    return ensure_all_bmc_sections(llm_text, simple_bmc, classification_summary)


def generate_sustainable_bmc_with_llm(bmc_json, sdg_predictions, rag_context):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not found")

    prompt = f"""
You are a sustainability-focused Business Model Canvas expert.

Your task is to transform the extracted Business Model Canvas into a Sustainable Business Model Canvas.

Input BMC:
{json.dumps(bmc_json, indent=2, ensure_ascii=False)}

Predicted SDGs:
{json.dumps(sdg_predictions, indent=2, ensure_ascii=False)}

Retrieved sustainability context:
{json.dumps(rag_context, indent=2, ensure_ascii=False)}

Rules:
- Keep the 9 official BMC blocks.
- Improve the business model with sustainability-oriented suggestions.
- Align recommendations with the predicted SDGs.
- Use the retrieved context as support.
- Add eco-friendly practices where relevant.
- Keep suggestions realistic.
- Keep sections concise.
- Return markdown sections, not JSON.

Output sections:
1. Key Partnerships
2. Key Activities
3. Key Resources
4. Value Proposition
5. Customer Relationships
6. Channels
7. Customer Segments
8. Cost Structure
9. Revenue Streams
10. Sustainability Improvements
11. Targeted SDGs
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a sustainability-focused Business Model Canvas expert."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 900,
        },
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Groq error {response.status_code}: {response.text}")

    data = response.json()
    sustainable_text = data["choices"][0]["message"]["content"]
    print("[SUSTAINABLE-BMC] Generation successful")
    return sustainable_text

# ==================== ROUTES ====================

@bmc_processor_bp.route("/extract-text", methods=["POST"])
def extract_text():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        image_file = request.files["file"]

        if image_file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        document_type = request.form.get("document_type", "auto").lower()
        ocr_method = request.form.get("ocr_method", "auto").lower()

        if ocr_method == "auto":
            ocr_method = "trocr" if document_type == "handwritten" else "easyocr"

        image_file.seek(0)
        raw_bytes = image_file.read()

        text = extract_text_from_image(
            _make_filelike(raw_bytes, image_file.filename),
            ocr_method=ocr_method,
        )

        return jsonify({
            "extracted_text": text,
            "status": "success",
        }), 200

    except Exception as e:
        print(f"✗ Error in /extract-text: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_processor_bp.route("/classify-text", methods=["POST"])
def classify_text():
    try:
        data = request.get_json(force=True)
        text = data.get("text", "")
        threshold = float(data.get("confidence_threshold", 0.55))

        classifications = classify_texts_with_distilbert([text], confidence_threshold=threshold)
        bmc_json = build_bmc_from_classifications(classifications)

        return jsonify({
            "classifications": classifications,
            "bmc_canvas": bmc_json,
            "classification_mode": "text_classifier_only",
            "status": "success",
        }), 200

    except Exception as e:
        print(f"✗ Error in /classify-text: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_processor_bp.route("/generate-sustainable-bmc", methods=["POST"])
def generate_sustainable_bmc():
    try:
        data = request.get_json(force=True) or {}
        bmc_json = data.get("bmc_json") or {}

        sdg_predictions = predict_sdgs_from_bmc(bmc_json)
        rag_query = bmc_to_text(bmc_json)
        if sdg_predictions:
            sdg_labels = ", ".join([p.get("sdg", "") for p in sdg_predictions if p.get("sdg")])
            rag_query = f"{rag_query}\nSDGs: {sdg_labels}".strip()

        rag_context = retrieve_sustainability_context(rag_query, top_k=4)

        try:
            sustainable_bmc = generate_sustainable_bmc_with_llm(
                bmc_json,
                sdg_predictions,
                rag_context,
            )
        except Exception as e:
            sustainable_bmc = f"Error: {e}"

        return jsonify({
            "sdg_predictions": sdg_predictions,
            "rag_context": rag_context,
            "sustainable_bmc": sustainable_bmc,
            "status": "success",
        }), 200

    except Exception as e:
        print(f"✗ Error in /generate-sustainable-bmc: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_processor_bp.route("/process-bmc", methods=["POST"])
def process_bmc():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        image_file = request.files["file"]

        if image_file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        confidence_threshold = float(request.form.get("confidence_threshold", 0.55))
        document_type = request.form.get("document_type", "auto").lower()
        ocr_method = request.form.get("ocr_method", "auto").lower()
        sustainable_flag = str(request.form.get("sustainable", "false")).lower() == "true"

        if ocr_method == "auto":
            ocr_method = "trocr" if document_type == "handwritten" else "easyocr"

        image_file.seek(0)
        raw_bytes = image_file.read()
        pil_image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

        # 1. Document classifier
        try:
            tensor = doc_preprocess_image(_make_filelike(raw_bytes, image_file.filename))
            doc_result = doc_predict_document_type(tensor)
            detected_doc_type = doc_result.get("document_type", document_type)
            detected_conf = float(doc_result.get("confidence", 0.0))

            # Prevent weak handwritten predictions from hijacking typed documents.
            all_probs = doc_result.get("all_probabilities", {}) if isinstance(doc_result, dict) else {}
            handwritten_prob = float(all_probs.get("handwritten", 0.0) or 0.0)
            typed_prob = float(all_probs.get("typed", 0.0) or 0.0)
            if detected_doc_type == "handwritten" and handwritten_prob < 0.70 and typed_prob >= 0.20:
                print(
                    "[DOC-POSTFIX] Overriding weak handwritten prediction -> typed "
                    f"(handwritten={handwritten_prob:.4f}, typed={typed_prob:.4f})"
                )
                detected_doc_type = "typed"
                detected_conf = typed_prob
        except Exception as e:
            print(f"⚠️ Document classifier failed: {e}")
            detected_doc_type = document_type
            detected_conf = 0.0

        is_bmc = detected_doc_type == "bmc" and detected_conf >= 0.5

        print("\n========== PROCESS-BMC ==========")
        print(f"File: {image_file.filename}")
        print(f"Document classifier -> type={detected_doc_type} confidence={detected_conf:.4f}")
        print(f"is_bmc={is_bmc}")
        print(f"ocr_method={ocr_method}")
        print("=================================\n")

        bmc_json = empty_bmc()
        extracted_text = ""
        classifications = []
        crop_debug = []
        yolo_detections = []
        classification_mode = "unknown"

        if is_bmc:
            # 2. YOLO detects blocks
            yolo_detections = detect_bmc_blocks(pil_image)

            if len(yolo_detections) > 0:
                classification_mode = "yolo_crops_ocr_distilbert"
                bmc_json, extracted_text, classifications, crop_debug = ocr_yolo_crops_then_classify(
                    pil_image,
                    yolo_detections,
                    ocr_method=ocr_method,
                    confidence_threshold=confidence_threshold,
                )
            else:
                # 3. Template fallback, still followed by DistilBERT
                classification_mode = "template_crops_ocr_distilbert"
                bmc_json, extracted_text, classifications, crop_debug = template_crops_then_classify(
                    pil_image,
                    ocr_method=ocr_method,
                    confidence_threshold=confidence_threshold,
                )
        else:
            # 4. Non-BMC fallback: page OCR + DistilBERT
            classification_mode = "page_ocr_distilbert"
            extracted_text = extract_text_from_image(
                _make_filelike(raw_bytes, image_file.filename),
                ocr_method=ocr_method,
                doc_type=detected_doc_type,
            )
            classifications = classify_texts_with_distilbert(
                [extracted_text],
                confidence_threshold=min(confidence_threshold, 0.25),
                require_confidence_without_hint=False,
            )
            bmc_json = build_bmc_from_classifications(classifications)

        print("FINAL CLASSIFICATION MODE:", classification_mode)
        print("YOLO DETECTIONS COUNT:", len(yolo_detections))

        # 5. Optional LLM
        use_llm = str(request.form.get("complete", "false")).lower() == "true"
        llm_output = None
        llm_status = "skipped"

        print(f"[LLM] complete flag received: {use_llm}")

        if use_llm:
            try:
                llm_output = generate_bmc_with_llm(bmc_json, classifications=classifications, classification_mode=classification_mode)
                if not llm_output:
                    llm_output = ensure_all_bmc_sections(
                        "",
                        simplify_bmc_json(bmc_json),
                        summarize_classifications(classifications),
                    )
                    llm_status = "fallback"
                else:
                    llm_status = "generated"
            except Exception as e:
                llm_output = ensure_all_bmc_sections(
                    "",
                    simplify_bmc_json(bmc_json),
                    summarize_classifications(classifications),
                )
                llm_status = "fallback"
                print(f"⚠️ LLM completion failed: {e}")
                traceback.print_exc()

        # Apply LLM backfill to empty blocks so UI canvas does not keep "No items classified" when completion is requested.
        if use_llm and llm_output:
            bmc_json = backfill_bmc_with_llm_sections(bmc_json, llm_output)

        sdg_predictions = []
        rag_context = []
        sustainable_bmc = None

        if use_llm and sustainable_flag:
            sdg_predictions = predict_sdgs_from_bmc(bmc_json)
            rag_query = bmc_to_text(bmc_json)
            if sdg_predictions:
                sdg_labels = ", ".join([p.get("sdg", "") for p in sdg_predictions if p.get("sdg")])
                rag_query = f"{rag_query}\nSDGs: {sdg_labels}".strip()

            rag_context = retrieve_sustainability_context(rag_query, top_k=4)

            try:
                sustainable_bmc = generate_sustainable_bmc_with_llm(
                    bmc_json,
                    sdg_predictions,
                    rag_context,
                )
            except Exception as e:
                sustainable_bmc = f"Error: {e}"

        response = {
            "extracted_text": extracted_text,
            "classifications": classifications,
            "bmc_canvas": bmc_json,
            "classification_mode": classification_mode,
            "document_type": detected_doc_type,
            "document_confidence": detected_conf,
            "yolo_detections_count": len(yolo_detections),
            "yolo_detections": yolo_detections,
            "crop_debug": crop_debug,
            "llm_status": llm_status,
            "status": "success",
        }

        if llm_output is not None:
            response["llm_output"] = llm_output

        if sustainable_flag:
            response["sdg_predictions"] = sdg_predictions
            response["rag_context"] = rag_context
            response["sustainable_bmc"] = sustainable_bmc

        return jsonify(response), 200

    except Exception as e:
        print(f"✗ Error in /process-bmc: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_processor_bp.route("/complete-bmc", methods=["POST"])
def complete_bmc():
    try:
        data = request.get_json(force=True)
        bmc_json = data.get("bmc_json")

        if not bmc_json:
            return jsonify({"error": "No bmc_json provided"}), 400

        llm_output = generate_bmc_with_llm(bmc_json)

        return jsonify({
            "llm_output": llm_output,
            "status": "success",
        }), 200

    except Exception as e:
        print(f"✗ Error in /complete-bmc: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_processor_bp.route("/model-info", methods=["GET"])
def model_info():
    yolo_model = load_yolo_model()

    yolo_classes = None
    if yolo_model is not None:
        yolo_classes = yolo_model.names

    return jsonify({
        "device": DEVICE,
        "bmc_blocks": BMC_BLOCKS,
        "text_classifier_path": TEXT_CLASSIFIER_PATH,
        "yolo_weights_path": YOLO_WEIGHTS_PATH,
        "yolo_classes": yolo_classes,
        "status": "success",
    }), 200


# ==================== INITIALIZATION ====================

def init_bmc_processor():
    print("\n📦 Initializing BMC Processor")
    print(f"Device: {DEVICE}")
    print(f"Text classifier path: {TEXT_CLASSIFIER_PATH}")
    print(f"YOLO weights path: {YOLO_WEIGHTS_PATH}")

    load_ocr_reader()
    load_text_classifier()
    load_yolo_model()

    print("✓ BMC Processor initialization finished\n")
    return True
