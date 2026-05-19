"""
BMC Evaluation Routes

Pipeline:
1. YOLO verifier checks if image is a BMC.
2. If BMC:
   - YOLO detector finds and crops 9 section boxes.
   - LSTM classifier decides typed vs handwritten per crop.
   - EasyOCR extracts text from typed crops.
   - TrOCR extracts text from handwritten crops.
3. RAG retrieves relevant passages from the BMC book.
4. Fine-tuned Llama 3.2-3B evaluates each section.
5. Returns full JSON evaluation (scores, feedback, coherence, SDG, overall).
"""

import io
import os
import re
import cv2
import json
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from flask import Blueprint, request, jsonify
from pathlib import Path
from torchvision import transforms

bmc_eval_bp = Blueprint("bmc_eval", __name__)

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR   = os.path.join(BASE_DIR, "bmc_eval_models")
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"

# ── Model paths ──────────────────────────────────────────────
VERIFIER_PATH     = os.path.join(MODELS_DIR, "bmc_verifier.pt")
DETECTOR_PATH     = os.path.join(MODELS_DIR, "bmc_detector.pt")
LSTM_PATH         = os.path.join(MODELS_DIR, "bmc_text_cnn_best.pt")
LSTM_CONFIG_PATH  = os.path.join(MODELS_DIR, "model_config.json")
LLAMA_ADAPTER_DIR = os.path.join(MODELS_DIR, "llama_bmc_adapter")
BMC_BOOK_DIR      = MODELS_DIR

LLAMA_BASE_MODEL  = "meta-llama/Llama-3.2-3B-Instruct"
TROCR_MODEL_NAME  = "microsoft/trocr-large-handwritten"
EMBED_MODEL_NAME  = "all-MiniLM-L6-v2"

CNN_CONF_THRESHOLD = 0.70

CLASS_NAMES = [
    "KeyPartners", "KeyActivities", "ValuePropositions",
    "CustomerRelationships", "CustomerSegments",
    "KeyResources", "Channels", "CostStructure", "RevenueStreams",
]

SECTION_DISPLAY = {
    "KeyPartners":           "Key Partners",
    "KeyActivities":         "Key Activities",
    "ValuePropositions":     "Value Propositions",
    "CustomerRelationships": "Customer Relationships",
    "CustomerSegments":      "Customer Segments",
    "KeyResources":          "Key Resources",
    "Channels":              "Channels",
    "CostStructure":         "Cost Structure",
    "RevenueStreams":         "Revenue Streams",
}

SYSTEM_PROMPT = (
    "You are an expert Business Model Canvas (BMC) evaluator and sustainability consultant. "
    "You evaluate BMCs on section quality (1-100), coherence between sections, "
    "sustainability (SDGs), and actionable improvements. Respond clearly and structured."
)

# ── Lazy-loaded globals ───────────────────────────────────────
_yolo_verifier   = None
_yolo_detector   = None
_lstm_model      = None
_easy_reader     = None
_trocr_processor = None
_trocr_model     = None
_rag_index       = None
_rag_chunks      = None
_rag_embedder    = None
_llama_tokenizer = None
_llama_model     = None


# ============================================================
# LSTM ARCHITECTURE  (must match Notebook 2 exactly)
# ============================================================

IMG_SIZE  = 224
N_PATCHES = 16
PATCH_H   = IMG_SIZE // N_PATCHES   # 14
PATCH_DIM = IMG_SIZE * PATCH_H * 3  # 9408


class _PatchEmbedding(nn.Module):
    def __init__(self, patch_dim, embed_dim, dropout=0.2):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(patch_dim, embed_dim, bias=False),
            nn.LayerNorm(embed_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.proj(x)


class _AttentionPooling(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.W = nn.Linear(hidden_size, hidden_size, bias=True)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, lstm_out):
        scores  = self.v(torch.tanh(self.W(lstm_out)))
        weights = F.softmax(scores.squeeze(-1), dim=1)
        context = (weights.unsqueeze(-1) * lstm_out).sum(dim=1)
        return context, weights


class _BMCTextLSTM(nn.Module):
    def __init__(self, patch_dim=PATCH_DIM, embed_dim=256,
                 hidden_size=256, num_layers=2, num_classes=2, dropout=0.3):
        super().__init__()
        self.patch_embed = _PatchEmbedding(patch_dim, embed_dim, dropout=0.2)
        self.lstm = nn.LSTM(
            input_size=embed_dim, hidden_size=hidden_size,
            num_layers=num_layers, batch_first=True,
            dropout=dropout, bidirectional=False,
        )
        self.attention  = _AttentionPooling(hidden_size)
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(hidden_size, 128),
            nn.LayerNorm(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, patches):
        embedded         = self.patch_embed(patches)
        lstm_out, _      = self.lstm(embedded)
        context, weights = self.attention(lstm_out)
        return self.classifier(context), weights


# ============================================================
# LOADERS
# ============================================================

def _load_yolo_verifier():
    global _yolo_verifier
    if _yolo_verifier is not None:
        return _yolo_verifier
    try:
        from ultralytics import YOLO
        if not os.path.exists(VERIFIER_PATH):
            print(f"[BMC-EVAL] Verifier not found: {VERIFIER_PATH}")
            return None
        _yolo_verifier = YOLO(VERIFIER_PATH)
        print("[BMC-EVAL] YOLO verifier loaded")
    except Exception as e:
        print(f"[BMC-EVAL] Verifier load failed: {e}")
    return _yolo_verifier


def _load_yolo_detector():
    global _yolo_detector
    if _yolo_detector is not None:
        return _yolo_detector
    try:
        from ultralytics import YOLO
        if not os.path.exists(DETECTOR_PATH):
            print(f"[BMC-EVAL] Detector not found: {DETECTOR_PATH}")
            return None
        _yolo_detector = YOLO(DETECTOR_PATH)
        print("[BMC-EVAL] YOLO detector loaded")
    except Exception as e:
        print(f"[BMC-EVAL] Detector load failed: {e}")
    return _yolo_detector


def _load_lstm():
    global _lstm_model
    if _lstm_model is not None:
        return _lstm_model
    try:
        if not os.path.exists(LSTM_PATH):
            print(f"[BMC-EVAL] LSTM not found: {LSTM_PATH}")
            return None

        checkpoint  = torch.load(LSTM_PATH, map_location=DEVICE)
        patch_dim   = checkpoint.get("patch_dim",   PATCH_DIM)
        embed_dim   = checkpoint.get("embed_dim",   256)
        hidden_size = checkpoint.get("hidden_size", 256)

        model = _BMCTextLSTM(
            patch_dim=patch_dim, embed_dim=embed_dim,
            hidden_size=hidden_size, num_layers=2,
            num_classes=2, dropout=0.3,
        ).to(DEVICE)

        state = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state)
        model.eval()
        _lstm_model = model
        print("[BMC-EVAL] LSTM classifier loaded")
    except Exception as e:
        print(f"[BMC-EVAL] LSTM load failed: {e}")
        traceback.print_exc()
    return _lstm_model


def _load_easyocr():
    global _easy_reader
    if _easy_reader is not None:
        return _easy_reader
    try:
        import easyocr
        _easy_reader = easyocr.Reader(["en"], gpu=(DEVICE == "cuda"), verbose=False)
        print("[BMC-EVAL] EasyOCR loaded")
    except Exception as e:
        print(f"[BMC-EVAL] EasyOCR load failed: {e}")
    return _easy_reader


def _load_trocr():
    global _trocr_processor, _trocr_model
    if _trocr_processor is not None:
        return _trocr_processor, _trocr_model
    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        _trocr_processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_NAME)
        _trocr_model     = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_NAME).to(DEVICE)
        _trocr_model.eval()
        print("[BMC-EVAL] TrOCR loaded")
    except Exception as e:
        print(f"[BMC-EVAL] TrOCR load failed: {e}")
        traceback.print_exc()
    return _trocr_processor, _trocr_model


def _load_rag():
    global _rag_index, _rag_chunks, _rag_embedder
    if _rag_index is not None:
        return _rag_index, _rag_chunks, _rag_embedder
    try:
        import faiss
        from sentence_transformers import SentenceTransformer

        pdf_files = list(Path(BMC_BOOK_DIR).glob("*.pdf"))
        if not pdf_files:
            print(f"[BMC-EVAL][RAG] No PDF found in {BMC_BOOK_DIR}")
            return None, [], None

        import fitz
        pages = []
        doc = fitz.open(str(pdf_files[0]))
        for page in doc:
            text = page.get_text("text").strip()
            if text:
                pages.append(text)
        doc.close()

        all_words = " ".join(pages).split()
        chunks, start = [], 0
        while start < len(all_words):
            end   = min(start + 500, len(all_words))
            chunks.append(" ".join(all_words[start:end]))
            start += 400

        _rag_embedder = SentenceTransformer(EMBED_MODEL_NAME)
        embeddings    = _rag_embedder.encode(chunks, show_progress_bar=False, batch_size=64)
        norms         = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings    = (embeddings / (norms + 1e-8)).astype(np.float32)

        _rag_index  = faiss.IndexFlatIP(embeddings.shape[1])
        _rag_index.add(embeddings)
        _rag_chunks = chunks

        print(f"[BMC-EVAL][RAG] Index built: {len(chunks)} chunks")
    except Exception as e:
        print(f"[BMC-EVAL][RAG] Load failed: {e}")
        traceback.print_exc()
    return _rag_index, _rag_chunks, _rag_embedder


def _load_llama():
    global _llama_tokenizer, _llama_model
    if _llama_model is not None:
        return _llama_tokenizer, _llama_model
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        hf_token = os.environ.get("HF_TOKEN", "")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        tok = AutoTokenizer.from_pretrained(
            LLAMA_BASE_MODEL, token=hf_token
        )
        tok.pad_token    = tok.eos_token
        tok.padding_side = "right"

        base = AutoModelForCausalLM.from_pretrained(
            LLAMA_BASE_MODEL,
            token=hf_token,
            quantization_config=bnb_config,
            device_map="auto",
        )
        base.config.use_cache = False

        if os.path.isdir(LLAMA_ADAPTER_DIR):
            model = PeftModel.from_pretrained(base, LLAMA_ADAPTER_DIR)
            print("[BMC-EVAL] Llama loaded with fine-tuned adapter")
        else:
            model = base
            print("[BMC-EVAL] Llama loaded (no adapter found — using base)")

        model.eval()
        _llama_tokenizer = tok
        _llama_model     = model
    except Exception as e:
        print(f"[BMC-EVAL] Llama load failed: {e}")
        traceback.print_exc()
    return _llama_tokenizer, _llama_model


# ============================================================
# HELPERS
# ============================================================

class _AdaptiveBinarize:
    def __call__(self, img):
        gray = np.array(img.convert("L"))
        if gray.mean() < 127:
            gray = cv2.bitwise_not(gray)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15, C=4,
        )
        return Image.fromarray(binary).convert("RGB")


_lstm_transform = transforms.Compose([
    _AdaptiveBinarize(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])


def _image_to_patches(tensor):
    C, H, W = tensor.shape
    patches = tensor.reshape(C, N_PATCHES, PATCH_H, W)
    patches = patches.permute(1, 0, 2, 3).reshape(N_PATCHES, -1)
    return patches


def _clean_text(raw):
    if not raw:
        return ""
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or len(line) < 2:
            continue
        alpha = sum(1 for c in line if c.isalnum() or c.isspace())
        if alpha / len(line) < 0.55:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _detect_language(text):
    french = {"les","des","une","pour","avec","nous","sont","dans","sur",
               "par","qui","que","est","notre","nos","leur","leurs","cette",
               "ces","partenaires","clients","revenus","coûts"}
    words = set(text.lower().split())
    return "fr" if len(words & french) >= 3 else "en"


def _retrieve(query, top_k=2):
    index, chunks, embedder = _load_rag()
    if index is None or not chunks:
        return []
    try:
        q = embedder.encode([query])
        q = (q / (np.linalg.norm(q) + 1e-8)).astype(np.float32)
        scores, idxs = index.search(q, top_k)
        return [{"text": chunks[i], "score": float(scores[0][j])}
                for j, i in enumerate(idxs[0]) if i < len(chunks)]
    except Exception as e:
        print(f"[BMC-EVAL][RAG] Retrieval error: {e}")
        return []


def _llm_generate(prompt, max_tokens=400):
    tok, model = _load_llama()
    if model is None:
        # ── LOCAL DEV FALLBACK: Llama unavailable ──────────
        return (
            "Score: 70/100\n"
            "Feedback: This section contains relevant content but could benefit from more specificity and detail.\n"
            "Improvement: Consider adding concrete examples, metrics, or named entities to strengthen this section."
        )
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=2048).to(DEVICE)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.15,
            pad_token_id=tok.eos_token_id,
        )
    new_ids = out[0][inputs["input_ids"].shape[1]:]
    return tok.decode(new_ids, skip_special_tokens=True).strip()


def _build_prompt(instruction, passages=None):
    context = ""
    if passages:
        context = "\n\n[Book Context]\n"
        for i, p in enumerate(passages, 1):
            context += f"[Passage {i}]: {p['text'][:350]}\n\n"
    return (
        f"<|begin_of_text|>"
        f"<|start_header_id|>system<|end_header_id|>\n{SYSTEM_PROMPT}\n"
        f"{context}"
        f"<|start_header_id|>user<|end_header_id|>\n{instruction}\n"
        f"<|start_header_id|>assistant<|end_header_id|>\n"
    )


def _parse_score(response):
    """
    Extract score from LLM response.
    Handles both 1-100 scale (Score: 75/100) and 1-5 scale (Score: 3/5 or Score: 3).
    Always returns a value in 1-100 range.
    """
    # Try X/100 first
    match = re.search(r'[Ss]core[:\s*]*(\d+)\s*/\s*100', response)
    if match:
        return max(1, min(100, int(match.group(1))))

    # Try X/5
    match = re.search(r'[Ss]core[:\s*]*(\d+)\s*/\s*5', response)
    if match:
        return max(1, min(100, int(match.group(1)) * 20))

    # Try bare number after Score: (assume 1-5 since model was trained on 1-5)
    match = re.search(r'[Ss]core[:\s*]*(\d+)', response)
    if match:
        raw = int(match.group(1))
        # If > 5 assume it's already 1-100
        if raw > 5:
            return max(1, min(100, raw))
        # Otherwise scale from 1-5 to 1-100
        return max(1, min(100, raw * 20))

    return 50  # fallback


def _parse_feedback_improvement(response):
    """
    Split LLM response into feedback and improvement.
    The model outputs paragraphs — we split at the first
    improvement/suggestion keyword line.
    Falls back to: first paragraph = feedback, rest = improvement.
    """
    # Try keyword-based split first
    lines = response.split("\n")
    split_keywords = [
        "improvement", "suggestion", "amélioration", "recommand",
        "to improve", "to enhance", "concrete improvement",
        "actionable", "starter", "what to add", "should contain",
    ]
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if any(kw in line.lower() for kw in split_keywords):
            feedback    = "\n".join(lines[:i]).strip()
            improvement = "\n".join(lines[i:]).strip()
            if feedback and improvement:
                return feedback, improvement

    # Fallback: split at first blank line after some content
    paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs[0], "\n\n".join(paragraphs[1:])

    # Last resort: everything is feedback
    return response.strip(), ""


# ============================================================
# PIPELINE STEPS
# ============================================================

def _verify_bmc(img_path):
    """Returns (is_bmc, bmc_conf, not_bmc_conf)."""
    verifier = _load_yolo_verifier()
    if verifier is None:
        return False, 0.0, 1.0
    yolo_device = "0" if torch.cuda.is_available() else "cpu"
    result   = verifier.predict(img_path, device=yolo_device, verbose=False)
    pred_cls = result[0].probs.top1
    bmc_conf     = float(result[0].probs.data[0])
    not_bmc_conf = float(result[0].probs.data[1])
    return (pred_cls == 0), bmc_conf, not_bmc_conf


def _detect_sections(img_path):
    """Returns list of detection dicts."""
    detector = _load_yolo_detector()
    if detector is None:
        return []
    yolo_device = "0" if torch.cuda.is_available() else "cpu"
    result = detector.predict(img_path, device=yolo_device, conf=0.25, verbose=False)
    boxes  = result[0].boxes
    if boxes is None or len(boxes) == 0:
        return []
    detections = []
    for box in boxes:
        cls_id = int(box.cls)
        detections.append({
            "class_id":   cls_id,
            "class_name": CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f"class_{cls_id}",
            "confidence": float(box.conf),
            "x1": int(box.xyxy[0][0]),
            "y1": int(box.xyxy[0][1]),
            "x2": int(box.xyxy[0][2]),
            "y2": int(box.xyxy[0][3]),
        })
    return detections


def _crop_sections(img_cv, detections, pad=5):
    """Returns {section_name: PIL_Image}."""
    h, w  = img_cv.shape[:2]
    crops = {}
    for det in detections:
        name = det["class_name"]
        x1c  = max(0, det["x1"] - pad)
        y1c  = max(0, det["y1"] - pad)
        x2c  = min(w, det["x2"] + pad)
        y2c  = min(h, det["y2"] + pad)
        crop = img_cv[y1c:y2c, x1c:x2c]
        if crop.size > 0:
            crops[name] = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    return crops


def _classify_crop(crop_pil):
    """Returns (text_type, confidence)."""
    model = _load_lstm()
    if model is None:
        return "typed", 0.0
    try:
        tensor  = _lstm_transform(crop_pil)
        patches = _image_to_patches(tensor).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            logits, _ = model(patches)
            probs = F.softmax(logits, dim=1)
            pred  = logits.argmax(1).item()
            conf  = float(probs[0][pred])
        return ("typed" if pred == 0 else "handwritten"), conf
    except Exception as e:
        print(f"[BMC-EVAL] LSTM classify error: {e}")
        return "typed", 0.0


def _run_easyocr(crop_pil):
    """Returns text string."""
    reader = _load_easyocr()
    if reader is None:
        return ""
    try:
        w, h = crop_pil.size
        if w < 800:
            scale    = 800 / w
            crop_pil = crop_pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        results = reader.readtext(np.array(crop_pil), detail=1, paragraph=False, min_size=10)
        good    = [(bbox, text, conf) for bbox, text, conf in results if conf > 0.30 and text.strip()]
        good.sort(key=lambda x: x[0][0][1])
        return _clean_text("\n".join(t for _, t, _ in good))
    except Exception as e:
        print(f"[BMC-EVAL] EasyOCR error: {e}")
        return ""


def _detect_text_lines(gray_np, min_line_height=10, merge_gap=8):
    _, binary = cv2.threshold(gray_np, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    row_sums  = binary.sum(axis=1)
    threshold = max(row_sums.max() * 0.04, 3)
    ink_rows  = np.where(row_sums > threshold)[0]
    if len(ink_rows) == 0:
        return []
    spans, start, prev = [], ink_rows[0], ink_rows[0]
    for r in ink_rows[1:]:
        if r - prev > merge_gap:
            if prev - start >= min_line_height:
                spans.append((start, prev))
            start = r
        prev = r
    if prev - start >= min_line_height:
        spans.append((start, prev))
    return spans


def _run_trocr(crop_pil):
    """Returns text string, line by line."""
    processor, model = _load_trocr()
    if processor is None:
        return ""
    try:
        w, h = crop_pil.size
        if w < 600:
            scale    = 600 / w
            crop_pil = crop_pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        gray_np    = np.array(crop_pil.convert("L"))
        line_spans = _detect_text_lines(gray_np) or [(0, gray_np.shape[0])]
        img_np     = np.array(crop_pil.convert("RGB"))
        lines_text = []

        for (y1, y2) in line_spans:
            y1p = max(0, y1 - 4)
            y2p = min(gray_np.shape[0], y2 + 4)
            line_crop = Image.fromarray(img_np[y1p:y2p, :])
            if line_crop.width < 10 or line_crop.height < 10:
                continue
            if line_crop.height < 32:
                pad       = (32 - line_crop.height) // 2
                line_crop = Image.fromarray(
                    cv2.copyMakeBorder(np.array(line_crop), pad, pad, 0, 0,
                                       cv2.BORDER_CONSTANT, value=(255, 255, 255))
                )
            pv = processor(images=line_crop.convert("RGB"), return_tensors="pt").pixel_values.to(DEVICE)
            with torch.no_grad():
                ids = model.generate(pv, max_new_tokens=64)
            text = processor.batch_decode(ids, skip_special_tokens=True)[0].strip()
            if text:
                lines_text.append(text)

        return _clean_text("\n".join(lines_text))
    except Exception as e:
        print(f"[BMC-EVAL] TrOCR error: {e}")
        return ""


def _evaluate_section(section_name, text, lang):
    display  = SECTION_DISPLAY.get(section_name, section_name)
    passages = _retrieve(f"How to evaluate {section_name} in a Business Model Canvas")
    is_empty = not text or len(text.strip()) < 5

    if is_empty:
        # Empty section — LLM gives advisory feedback, score is fixed at 0
        if lang == "fr":
            instruction = (
                f"La section '{display}' du Business Model Canvas est vide.\n\n"
                f"Fournissez:\n"
                f"1. Pourquoi cette section est-elle essentielle dans un BMC?\n"
                f"2. Que doit-elle contenir concrètement? (2-3 exemples)\n"
                f"3. Une suggestion de démarrage pour remplir cette section.\n"
                f"Répondez en français."
            )
        else:
            instruction = (
                f"The '{display}' section of this Business Model Canvas is empty.\n\n"
                f"Provide:\n"
                f"1. Why is this section essential in a BMC?\n"
                f"2. What should it concretely contain? (2-3 examples)\n"
                f"3. A starter suggestion to fill this section.\n"
                f"Respond in English."
            )
        response = _llm_generate(_build_prompt(instruction, passages), max_tokens=300)
        feedback, improvement = _parse_feedback_improvement(response)
        return {"score": 0, "feedback": feedback, "improvement": improvement, "was_empty": True}

    # Non-empty section
    if lang == "fr":
        instruction = (
            f"Évaluez cette section '{display}' d'un Business Model Canvas:\n\n"
            f"\"{text}\"\n\n"
            f"Fournissez exactement:\n"
            f"Score: X/100\n"
            f"Feedback: [évaluation détaillée en 2-3 phrases]\n"
            f"Amélioration: [suggestion concrète en 2-3 phrases]\n"
            f"Répondez en français."
        )
    else:
        instruction = (
            f"Evaluate this '{display}' section of a Business Model Canvas:\n\n"
            f"\"{text}\"\n\n"
            f"Provide exactly:\n"
            f"Score: X/100\n"
            f"Feedback: [detailed evaluation in 2-3 sentences]\n"
            f"Improvement: [one concrete improvement suggestion in 2-3 sentences]\n"
            f"Respond in English."
        )

    response = _llm_generate(_build_prompt(instruction, passages), max_tokens=350)
    print(f"[BMC-EVAL][DEBUG] Raw LLM response for {section_name}:\n{response}\n---END---")

    score    = _parse_score(response)

    # Remove the score line before parsing feedback/improvement
    response_no_score = re.sub(r'[Ss]core[:\s*]*\d+\s*(?:/\s*\d+)?\s*\n?', '', response).strip()
    feedback, improvement = _parse_feedback_improvement(response_no_score)

    return {"score": score, "feedback": feedback, "improvement": improvement, "was_empty": False}


def _evaluate_coherence(sections_text, lang):
    summary = "\n".join([
        f"- {SECTION_DISPLAY.get(k, k)}: {v[:120].replace(chr(10), ' ')}"
        for k, v in sections_text.items() if v.strip()
    ]) or "(All sections empty)"

    passages = _retrieve("BMC coherence alignment between sections")

    if lang == "fr":
        instruction = (
            f"Analysez la cohérence de ce BMC:\n{summary}\n\n"
            f"Fournissez exactement:\n"
            f"Score de cohérence: X/100\n"
            f"Points forts: [alignements détectés]\n"
            f"Contradictions: [incohérences détectées]\n"
            f"Recommandations: [actions concrètes]\n"
            f"Répondez en français."
        )
    else:
        instruction = (
            f"Analyze coherence of this BMC:\n{summary}\n\n"
            f"Provide exactly:\n"
            f"Coherence Score: X/100\n"
            f"Strong points: [detected alignments]\n"
            f"Contradictions: [detected inconsistencies]\n"
            f"Recommendations: [concrete actions]\n"
            f"Respond in English."
        )

    response = _llm_generate(_build_prompt(instruction, passages), max_tokens=400)

    # Parse coherence score — handles X/100, X/5, or bare X
    match_100 = re.search(r'[Cc]oherence\s+[Ss]core[:\s]+(\d+)\s*/\s*100|[Ss]core\s+de\s+coh[eé]rence[:\s]+(\d+)\s*/\s*100', response)
    match_5   = re.search(r'[Cc]oherence\s+[Ss]core[:\s]+(\d+)\s*/\s*5|[Ss]core\s+de\s+coh[eé]rence[:\s]+(\d+)\s*/\s*5', response)
    match_bare= re.search(r'[Cc]oherence\s+[Ss]core[:\s]+(\d+)|[Ss]core\s+de\s+coh[eé]rence[:\s]+(\d+)', response)

    if match_100:
        raw = int(match_100.group(1) or match_100.group(2))
        score = max(1, min(100, raw))
    elif match_5:
        raw = int(match_5.group(1) or match_5.group(2))
        score = max(1, min(100, raw * 20))
    elif match_bare:
        raw = int(match_bare.group(1) or match_bare.group(2))
        score = max(1, min(100, raw * 20)) if raw <= 5 else max(1, min(100, raw))
    else:
        score = 50

    return {"score": score, "analysis": response}


def _evaluate_sustainability(sections_text, lang):
    key_sections = "\n".join([
        f"- {SECTION_DISPLAY.get(k, k)}: {sections_text.get(k, '')[:120]}"
        for k in ["KeyActivities", "ValuePropositions", "CostStructure",
                  "KeyPartners", "RevenueStreams"]
        if sections_text.get(k, "").strip()
    ]) or "(No content available)"

    passages = _retrieve("sustainability SDG zero carbon business model canvas")

    if lang == "fr":
        instruction = (
            f"Analysez ce BMC pour les opportunités de durabilité:\n{key_sections}\n\n"
            f"1. État actuel\n2. Top 3 ODD\n3. Feuille de route zéro carbone\n"
            f"Répondez en français."
        )
    else:
        instruction = (
            f"Analyze this BMC for sustainability:\n{key_sections}\n\n"
            f"1. Current state\n2. Top 3 SDGs\n3. Zero-carbon roadmap\n"
            f"Respond in English."
        )

    response = _llm_generate(_build_prompt(instruction, passages), max_tokens=450)
    return {"advice": response}


def _generate_overall(section_scores, coherence_score, lang):
    # Exclude empty sections (score=0) from average
    scored = {k: v for k, v in section_scores.items() if v > 0}
    avg     = sum(scored.values()) / max(len(scored), 1)
    overall = round(0.6 * avg + 0.4 * coherence_score, 1)
    bottom3 = sorted(section_scores.items(), key=lambda x: x[1])[:3]
    priority = ", ".join(f"{SECTION_DISPLAY.get(s, s)} ({sc}/100)" for s, sc in bottom3)

    if lang == "fr":
        instruction = (
            f"Générez un résumé exécutif:\n"
            f"Scores: {json.dumps({SECTION_DISPLAY.get(k,k): v for k,v in section_scores.items()})}\n"
            f"Cohérence: {coherence_score}/100 | Global: {overall}/100 | Priorités: {priority}\n"
            f"Résumé 3-4 phrases + top 3 priorités + points forts. Répondez en français."
        )
    else:
        instruction = (
            f"Generate executive summary:\n"
            f"Scores: {json.dumps({SECTION_DISPLAY.get(k,k): v for k,v in section_scores.items()})}\n"
            f"Coherence: {coherence_score}/100 | Overall: {overall}/100 | Priorities: {priority}\n"
            f"3-4 sentence summary + top 3 priorities + key strengths. Respond in English."
        )

    response = _llm_generate(_build_prompt(instruction), max_tokens=350)
    return {
        "score":       overall,
        "section_avg": round(avg, 1),
        "coherence":   coherence_score,
        "summary":     response,
        "priorities":  [s for s, _ in bottom3],
    }


# ============================================================
# ROUTES
# ============================================================

@bmc_eval_bp.route("/evaluate-bmc", methods=["POST"])
def evaluate_bmc():
    """
    POST /api/evaluate-bmc
    Body: multipart/form-data with field 'file' (image)
    Returns: full JSON evaluation
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        image_file = request.files["file"]
        if image_file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        import tempfile
        suffix = os.path.splitext(image_file.filename)[1] or ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        image_file.save(tmp.name)
        tmp_path = tmp.name
        tmp.close()

        result = {
            "image":          image_file.filename,
            "is_bmc":         False,
            "bmc_confidence": 0.0,
            "error":          None,
            "sections":       {},
            "coherence":      {},
            "sustainability": {},
            "overall":        {},
            "language":       "en",
        }

        # Step 1: Verify
        print(f"[BMC-EVAL] Step 1: Verifying {image_file.filename}")
        is_bmc, bmc_conf, not_bmc_conf = _verify_bmc(tmp_path)
        result["is_bmc"]         = is_bmc
        result["bmc_confidence"] = round(bmc_conf, 4)

        if not is_bmc:
            result["error"] = f"Not a BMC ({not_bmc_conf:.2%} confidence)"
            print(f"[BMC-EVAL] Rejected — not a BMC")
            os.unlink(tmp_path)
            return jsonify(result), 200

        print(f"[BMC-EVAL] Confirmed BMC ({bmc_conf:.2%})")

        # Step 2: Detect and crop
        print("[BMC-EVAL] Step 2: Detecting sections")
        img_cv     = cv2.imread(tmp_path)
        detections = _detect_sections(tmp_path)
        crops      = _crop_sections(img_cv, detections)
        print(f"[BMC-EVAL] Detected {len(crops)}/9 sections")

        if not crops:
            result["error"] = "No sections detected"
            os.unlink(tmp_path)
            return jsonify(result), 200

        # Step 3+4: Classify and extract text
        print("[BMC-EVAL] Step 3+4: Classify + OCR")
        sections_text = {}
        sections_meta = {}

        for section_name, crop_pil in crops.items():
            text_type, cnn_conf = _classify_crop(crop_pil)
            if cnn_conf < CNN_CONF_THRESHOLD:
                text_type = "typed"

            if text_type == "typed":
                text   = _run_easyocr(crop_pil)
                engine = "easyocr"
            else:
                text   = _run_trocr(crop_pil)
                engine = "trocr"

            sections_text[section_name] = text
            sections_meta[section_name] = {
                "text_type":      text_type,
                "cnn_confidence": round(cnn_conf, 4),
                "engine":         engine,
                "word_count":     len(text.split()),
            }
            icon = "✅" if text.strip() else "❌"
            print(f"[BMC-EVAL] {icon} {section_name:<25} [{text_type}] {len(text.split())}w via {engine}")

        os.unlink(tmp_path)

        # Step 5: Language detection
        all_text = " ".join(sections_text.values())
        lang     = _detect_language(all_text)
        result["language"] = lang
        print(f"[BMC-EVAL] Language: {'French' if lang=='fr' else 'English'}")

        # Step 6: Evaluate sections
        print("[BMC-EVAL] Step 6: LLM section evaluation")
        section_scores  = {}
        section_results = {}

        for section_name in CLASS_NAMES:
            text        = sections_text.get(section_name, "")
            eval_result = _evaluate_section(section_name, text, lang)
            section_scores[section_name]  = eval_result["score"]
            section_results[section_name] = {
                **sections_meta.get(section_name, {}),
                "text":        text,
                "score":       eval_result["score"],
                "feedback":    eval_result["feedback"],
                "improvement": eval_result["improvement"],
            }
            print(f"[BMC-EVAL] {section_name:<25}: {eval_result['score']}/100")

        result["sections"] = section_results

        # Step 7a: Coherence
        print("[BMC-EVAL] Step 7a: Coherence")
        coherence           = _evaluate_coherence(sections_text, lang)
        result["coherence"] = coherence

        # Step 7b: Sustainability
        print("[BMC-EVAL] Step 7b: Sustainability")
        result["sustainability"] = _evaluate_sustainability(sections_text, lang)

        # Step 7c: Overall
        print("[BMC-EVAL] Step 7c: Overall")
        result["overall"] = _generate_overall(section_scores, coherence["score"], lang)

        print(f"[BMC-EVAL] Done. Overall: {result['overall'].get('score')}/100")
        return jsonify(result), 200

    except Exception as e:
        print(f"[BMC-EVAL] Error in /evaluate-bmc: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bmc_eval_bp.route("/bmc-eval-health", methods=["GET"])
def bmc_eval_health():
    return jsonify({
        "status":  "ok",
        "models": {
            "yolo_verifier": os.path.exists(VERIFIER_PATH),
            "yolo_detector": os.path.exists(DETECTOR_PATH),
            "lstm":          os.path.exists(LSTM_PATH),
            "llama_adapter": os.path.isdir(LLAMA_ADAPTER_DIR),
        },
        "device": DEVICE,
    }), 200


@bmc_eval_bp.route("/bmc-eval-model-info", methods=["GET"])
def bmc_eval_model_info():
    return jsonify({
        "verifier_path":     VERIFIER_PATH,
        "detector_path":     DETECTOR_PATH,
        "lstm_path":         LSTM_PATH,
        "llama_adapter_dir": LLAMA_ADAPTER_DIR,
        "llama_base_model":  LLAMA_BASE_MODEL,
        "trocr_model":       TROCR_MODEL_NAME,
        "embed_model":       EMBED_MODEL_NAME,
        "device":            DEVICE,
        "class_names":       CLASS_NAMES,
    }), 200


# ============================================================
# INITIALIZATION
# ============================================================

def init_bmc_eval():
    print("\n📦 Initializing BMC Evaluation Module")
    print(f"   Device      : {DEVICE}")
    print(f"   Models dir  : {MODELS_DIR}")

    _load_yolo_verifier()
    _load_yolo_detector()
    _load_lstm()
    _load_easyocr()

    print("   TrOCR / RAG / Llama: lazy load on first request")
    print("✓ BMC Evaluation Module initialized\n")
    return True