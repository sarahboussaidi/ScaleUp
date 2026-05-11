import os
import json
from typing import Dict, Any
import numpy as np

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except Exception:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    torch = None

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "final_distilbert_pitch_strength_74")
HATE_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "distilbert_hate_final_v2")
STRONG_KEYWORDS = os.path.join(os.path.dirname(__file__), "models", "strong_keywords_weights.json")
WEAK_KEYWORDS = os.path.join(os.path.dirname(__file__), "models", "weak_keywords.json")

TOXIC_KEYWORDS = [
    "hate",
    "toxic",
    "abusive",
    "offensive",
    "idiot",
    "stupid",
    "moron",
    "fool",
    "fuck",
    "shit",
    "bitch",
    "asshole",
]

_model = None
_tokenizer = None
_hate_model = None
_hate_tokenizer = None
_strong_kw = {}
_weak_kw = {}
_loading = False

def load_resources():
    global _model, _tokenizer, _hate_model, _hate_tokenizer, _strong_kw, _weak_kw, _loading
    if AutoTokenizer is None:
        raise ImportError("transformers not available")

    if _model is None and not _loading:
        _loading = True
        print("[*] Loading DistilBERT model (this may take 30-60s on first run)...")
        if not os.path.isdir(MODEL_DIR):
            raise FileNotFoundError(f"Model dir not found: {MODEL_DIR}")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        _model.eval()
        print("[OK] DistilBERT model loaded successfully")

    if _hate_model is None and os.path.isdir(HATE_MODEL_DIR):
        try:
            _hate_tokenizer = AutoTokenizer.from_pretrained(HATE_MODEL_DIR)
            _hate_model = AutoModelForSequenceClassification.from_pretrained(HATE_MODEL_DIR)
            _hate_model.eval()
            print("[OK] Toxicity model loaded successfully")
        except Exception as e:
            print(f"[WARN] Toxicity model load skipped: {e}")

    # load keywords if present
    try:
        if os.path.exists(STRONG_KEYWORDS):
            with open(STRONG_KEYWORDS, 'r', encoding='utf-8') as f:
                _strong_kw = json.load(f)
    except Exception:
        _strong_kw = {}

    try:
        if os.path.exists(WEAK_KEYWORDS):
            with open(WEAK_KEYWORDS, 'r', encoding='utf-8') as f:
                _weak_kw = json.load(f)
    except Exception:
        _weak_kw = {}


def bert_predict_prob(text: str) -> float:
    load_resources()
    global _model, _tokenizer
    inputs = _tokenizer(text, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        outputs = _model(**inputs)
        # assume model returns logits for 3 classes [weak, moderate, strong]
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        # probability for 'strong' class
        # if label order unknown, take max as strength proxy normalized
        # here we prefer index 2 as strong if model trained that way
        if probs.shape[0] == 3:
            strong_prob = float(probs[2])
        else:
            strong_prob = float(np.max(probs))
    return strong_prob


def keyword_score(text: str) -> float:
    # score in [0,1] where presence of strong keywords increases score, weak keywords decreases
    txt = text.lower()
    score = 0.0
    max_score = 0.0
    for k, w in _strong_kw.items():
        max_score += abs(float(w))
        if k.lower() in txt:
            score += float(w)
    for k, w in _weak_kw.items():
        max_score += abs(float(w))
        if k.lower() in txt:
            score -= float(w)

    if max_score <= 0:
        return 0.5
    # normalize to [0,1]
    norm = (score + max_score) / (2 * max_score)
    return float(max(0.0, min(1.0, norm)))


def length_score(text: str) -> float:
    # Prefer moderate length: 30-200 words
    words = text.split()
    n = len(words)
    if n <= 10:
        return 0.0
    if n >= 200:
        return 1.0
    # linear mapping 10..200 -> 0..1
    return float((n - 10) / (200 - 10))


def structure_score(text: str) -> float:
    # naive heuristic: count sentences and punctuation
    sentences = [s for s in text.split('.') if s.strip()]
    n_sent = len(sentences)
    if n_sent == 0:
        return 0.0
    # if sentences are reasonable (2-10) -> higher
    if n_sent <= 1:
        return 0.0
    if n_sent >= 12:
        return 1.0
    return float(min(1.0, n_sent / 12.0))


def toxicity_keyword_hits(text: str):
    txt = text.lower()
    return [keyword for keyword in TOXIC_KEYWORDS if keyword in txt]


def bert_toxicity_prob(text: str) -> float:
    try:
        load_resources()
    except Exception:
        return 0.5

    if _hate_model is None or _hate_tokenizer is None or torch is None:
        return 0.5

    try:
        inputs = _hate_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = _hate_model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        if probs.shape[0] == 1:
            return float(probs[0])

        if probs.shape[0] >= 2:
            labels = getattr(_hate_model.config, "id2label", {}) or {}
            toxic_index = None
            for index, label in labels.items():
                label_text = str(label).lower()
                if any(marker in label_text for marker in ("toxic", "hate", "offensive", "abusive")):
                    toxic_index = int(index)
                    break
            if toxic_index is None:
                toxic_index = min(1, len(probs) - 1)
            return float(probs[toxic_index])
    except Exception:
        return 0.5

    return 0.5


def hybrid_strength_predict(text: str) -> Dict[str, Any]:
    """
    Combine BERT probability (40%) + keyword (40%) + length (10%) + structure (10%)
    Returns label and final_score in [0,1]
    """
    try:
        bert_p = bert_predict_prob(text)
    except Exception:
        bert_p = 0.5

    try:
        kw = keyword_score(text)
    except Exception:
        kw = 0.5

    try:
        ls = length_score(text)
    except Exception:
        ls = 0.5

    try:
        ss = structure_score(text)
    except Exception:
        ss = 0.5

    final_score = 0.4 * bert_p + 0.4 * kw + 0.1 * ls + 0.1 * ss

    if final_score < 0.4:
        label = "weak"
    elif final_score < 0.7:
        label = "moderate"
    else:
        label = "strong"

    details = {
        "bert_prob": bert_p,
        "keyword_score": kw,
        "length_score": ls,
        "structure_score": ss,
    }

    return {"label": label, "final_score": float(final_score), "details": details}


def detect_bad_words(text: str) -> Dict[str, Any]:
    """Detect toxic or bad-word content from the transcript."""
    try:
        keyword_hits = toxicity_keyword_hits(text)
        keyword_score = min(1.0, len(keyword_hits) / 3.0)
        model_prob = bert_toxicity_prob(text)

        final_score = (0.65 * keyword_score) + (0.35 * model_prob)
        if keyword_hits:
            label = "toxic"
        else:
            label = "toxic" if final_score >= 0.55 else "clean"

        return {
            "label": label,
            "confidence": float(final_score),
            "details": {
                "keyword_hits": keyword_hits,
                "keyword_score": float(keyword_score),
                "model_prob": float(model_prob),
            },
        }
    except Exception:
        return {
            "label": "clean",
            "confidence": 0.0,
            "details": {
                "keyword_hits": [],
                "keyword_score": 0.0,
                "model_prob": 0.0,
            },
        }


if __name__ == "__main__":
    # quick test
    load_resources()
    print(hybrid_strength_predict("This is a quick practice pitch with clear structure and solid keywords."))
