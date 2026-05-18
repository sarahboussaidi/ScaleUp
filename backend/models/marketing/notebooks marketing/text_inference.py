import json
import os
from PIL import Image
import re

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import easyocr
except Exception:
    easyocr = None

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:
    RapidOCR = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import torch
except Exception:
    torch = None

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
except Exception:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None

# Default pretrained sentiment model used in the notebook
DEFAULT_SENT_MODEL = 'cardiffnlp/twitter-roberta-base-sentiment-latest'

# Module-level cache for the transformer sentiment model
_sent_tokenizer = None
_sent_model = None
_sent_label_map = None
_rapidocr_engine = None

import warnings


def _ensure_rapidocr_loaded():
    global _rapidocr_engine
    if RapidOCR is None:
        return None
    if _rapidocr_engine is None:
        try:
            _rapidocr_engine = RapidOCR()
        except Exception:
            _rapidocr_engine = None
    return _rapidocr_engine


def _rapidocr_extract_words(image_path):
    engine = _ensure_rapidocr_loaded()
    if engine is None:
        return []

    try:
        results, _ = engine(image_path)
    except Exception:
        return []

    words = []
    for item in results or []:
        try:
            box, text, confidence = item
        except Exception:
            continue
        cleaned = (text or '').strip()
        if not cleaned:
            continue
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0
        if confidence < 0.20:
            continue
        try:
            xs = [point[0] for point in box]
            ys = [point[1] for point in box]
            center_x = sum(xs) / max(1, len(xs))
            center_y = sum(ys) / max(1, len(ys))
        except Exception:
            center_x = 0.0
            center_y = 0.0
        words.append((cleaned, center_x, center_y))
    return words


def extract_text_from_image(image_path):
    """Extract visible text from an image using pytesseract or easyocr (fallback).

    Tries multiple OCR engines in order:
    1. pytesseract (uses system Tesseract)
    2. easyocr (pure Python, slower but no system deps)
    3. Returns empty string if no OCR available
    
    Returns the raw text string (may be empty).
    """
    
    # Try pytesseract first (fastest if Tesseract is installed)
    if pytesseract is not None:
        try:
            img = Image.open(image_path).convert("RGB")
            text = pytesseract.image_to_string(img, lang='eng')
            if text.strip():
                return text.strip()
        except Exception as e:
            pass  # Try next engine
    
    # Fall back to easyocr (no system deps, but slower)
    if easyocr is not None:
        try:
            import cv2
            import numpy as np
            # Read image with cv2 and preprocess
            img_cv = cv2.imread(image_path)
            if img_cv is not None:
                # Enhance contrast to help text detection
                lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
                
                # Run OCR on enhanced image
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                results = reader.readtext(enhanced)
                if results:
                    text = '\n'.join([item[1] for item in results])
                    if text.strip():
                        return text.strip()
        except Exception as e:
            # Fallback: try easyocr without preprocessing
            try:
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                results = reader.readtext(image_path)
                if results:
                    text = '\n'.join([item[1] for item in results])
                    if text.strip():
                        return text.strip()
            except Exception:
                pass

    # Final fallback: RapidOCR (works in the ScaleUp Windows environment)
    if RapidOCR is not None:
        try:
            engine = _ensure_rapidocr_loaded()
            if engine is not None:
                results, _ = engine(image_path)
                if results:
                    text = '\n'.join([(item[1] or '').strip() for item in results if (item[1] or '').strip()])
                    if text.strip():
                        return text.strip()
        except Exception:
            pass
    
    # If both fail, return empty (graceful degradation)
    return ""


def extract_text_regions_from_image(image_path):
    """Extract OCR text grouped by coarse screenshot regions.

    Returns a dict with the full text plus region buckets such as top,
    middle, bottom, left, center, and right. This is used by platform
    detection to give more weight to layout-specific signals.
    """
    regions = {
        'full_text': '',
        'top': '',
        'middle': '',
        'bottom': '',
        'left': '',
        'center': '',
        'right': '',
    }

    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size
    except Exception:
        return regions

    words = []

    if pytesseract is not None:
        try:
            data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)
            for index, text in enumerate(data.get('text', [])):
                cleaned = (text or '').strip()
                if not cleaned:
                    continue
                try:
                    confidence = float(data.get('conf', ['-1'])[index])
                except Exception:
                    confidence = -1.0
                if confidence < 0:
                    continue

                left = int(data.get('left', [0])[index])
                top = int(data.get('top', [0])[index])
                box_width = int(data.get('width', [0])[index])
                box_height = int(data.get('height', [0])[index])
                center_x = left + box_width / 2.0
                center_y = top + box_height / 2.0
                words.append((cleaned, center_x, center_y))
        except Exception:
            words = []

    if not words and easyocr is not None:
        try:
            import cv2

            img_cv = cv2.imread(image_path)
            if img_cv is not None:
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                results = reader.readtext(img_cv)
                for item in results or []:
                    box, text, confidence = item
                    cleaned = (text or '').strip()
                    if not cleaned:
                        continue
                    if confidence is not None and float(confidence) < 0.20:
                        continue
                    xs = [point[0] for point in box]
                    ys = [point[1] for point in box]
                    center_x = sum(xs) / max(1, len(xs))
                    center_y = sum(ys) / max(1, len(ys))
                    words.append((cleaned, center_x, center_y))
        except Exception:
            words = []

    if not words and RapidOCR is not None:
        try:
            words = _rapidocr_extract_words(image_path)
        except Exception:
            words = []

    if not words:
        fallback = extract_text_from_image(image_path)
        regions['full_text'] = fallback
        regions['middle'] = fallback
        return regions

    full_text = ' '.join(word for word, _, _ in words)
    region_buckets = {
        'top': [],
        'middle': [],
        'bottom': [],
        'left': [],
        'center': [],
        'right': [],
    }

    for word, center_x, center_y in words:
        x_ratio = center_x / max(1.0, width)
        y_ratio = center_y / max(1.0, height)

        if y_ratio < 0.33:
            region_buckets['top'].append(word)
        elif y_ratio < 0.66:
            region_buckets['middle'].append(word)
        else:
            region_buckets['bottom'].append(word)

        if x_ratio < 0.33:
            region_buckets['left'].append(word)
        elif x_ratio < 0.66:
            region_buckets['center'].append(word)
        else:
            region_buckets['right'].append(word)

    regions['full_text'] = full_text
    for key, value in region_buckets.items():
        regions[key] = ' '.join(value)

    return regions


def evaluate_text_features(raw_text):
    """Compute simple text features used by downstream models.

    Returns a dict with simple signals: word_count, hashtag_count,
    mention_count, sentiment_polarity, avg_word_len.
    """
    text = raw_text or ""
    words = re.findall(r"\w+", text)
    word_count = len(words)
    char_count = len(text)
    hashtag_count = text.count("#")
    mention_count = text.count("@")
    avg_word_len = (sum(len(w) for w in words) / word_count) if word_count else 0.0

    # Sentiment is now only computed via transformer model (see _score_sentiment function)
    sentiment = 0.0

    return {
        "raw_text": text,
        "word_count": int(word_count),
        "char_count": int(char_count),
        "hashtag_count": int(hashtag_count),
        "mention_count": int(mention_count),
        "avg_word_len": float(avg_word_len),
        "sentiment_polarity": float(sentiment),
    }


DEFAULT_OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_text_module_artifacts(outputs_dir=None):
    """Load notebook artifacts for the text module."""
    outputs_dir = outputs_dir or DEFAULT_OUTPUTS_DIR
    module_config = _load_json(os.path.join(outputs_dir, "text_module_config.json"), default={}) or {}
    benchmark_config = _load_json(os.path.join(outputs_dir, "platform_text_benchmarks.json"), default={}) or {}
    feature_config = _load_json(os.path.join(outputs_dir, "text_feature_config.json"), default={}) or {}
    return {
        "module_config": module_config,
        "benchmarks": benchmark_config,
        "feature_config": feature_config,
    }


def _safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _count_syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    vowels = "aeiouy"
    groups = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            groups += 1
        prev_vowel = is_vowel
    if word.endswith("e") and groups > 1:
        groups -= 1
    return max(1, groups)


def _flesch_reading_ease(text):
    words = re.findall(r"\w+", text)
    sentences = re.split(r"[.!?]+", text)
    sentence_count = max(1, len([s for s in sentences if s.strip()]))
    word_count = max(1, len(words))
    syllable_count = sum(_count_syllables(word) for word in words)
    return 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)


def _ensure_sentiment_model_loaded(model_name=None, device=None):
    global _sent_tokenizer, _sent_model, _sent_label_map
    if AutoTokenizer is None or AutoModelForSequenceClassification is None:
        return False
    if _sent_model is not None and _sent_tokenizer is not None:
        return True
    model_name = model_name or DEFAULT_SENT_MODEL
    if device is None:
        device = 'cpu'
        try:
            if torch is not None and torch.cuda.is_available():
                device = 'cuda'
        except Exception:
            device = 'cpu'
    try:
        _sent_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _sent_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        if torch is not None:
            _sent_model.to(device)
        cfg = getattr(_sent_model, 'config', None)
        if cfg is not None and hasattr(cfg, 'id2label'):
            _sent_label_map = {int(k): str(v).lower() for k, v in cfg.id2label.items()}
        else:
            _sent_label_map = None
        return True
    except Exception:
        _sent_tokenizer = None
        _sent_model = None
        _sent_label_map = None
        return False


def _extract_text_metrics(raw_text):
    text = raw_text or ""
    words = re.findall(r"\w+", text)
    lower = text.lower()
    hashtags = re.findall(r"#\w+", text)
    mentions = re.findall(r"@\w+", text)
    exclaim_count = text.count("!")
    question_count = text.count("?")
    emoji_count = sum(1 for char in text if ord(char) > 10000)
    has_cta = 1 if any(word in lower for word in ["buy", "link", "click", "subscribe", "swipe", "dm", "shop", "book", "reserve", "try", "learn more", "sign up"]) else 0
    has_url = 1 if re.search(r"https?://|www\\.", text, re.IGNORECASE) else 0
    sentence_count = max(1, len([s for s in re.split(r"[.!?]+", text) if s.strip()]))
    caps_tokens = [token for token in re.findall(r"[A-Za-zÀ-ÿ]+", text) if len(token) >= 3 and token.isupper()]
    caps_ratio = _safe_div(len(caps_tokens), max(1, len(re.findall(r"[A-Za-zÀ-ÿ]+", text))))
    unique_hashtag_ratio = _safe_div(len(set(hashtags)), len(hashtags))
    readability_flesch = _flesch_reading_ease(text) if text.strip() else 0.0
    avg_word_length = _safe_div(sum(len(word) for word in words), len(words))

    return {
        "raw_text": text,
        "word_count": len(words),
        "char_count": len(text),
        "hashtag_count": len(hashtags),
        "mention_count": len(mentions),
        "exclaim_count": exclaim_count,
        "question_count": question_count,
        "emoji_count": emoji_count,
        "has_cta": has_cta,
        "has_url": has_url,
        "readability_flesch": float(readability_flesch),
        "avg_word_length": float(avg_word_length),
        "sentence_count": sentence_count,
        "caps_ratio": float(caps_ratio),
        "unique_hashtag_ratio": float(unique_hashtag_ratio),
    }


def _score_readability(feats):
    flesch = float(feats.get("readability_flesch", 0.0))
    avg_word_len = float(feats.get("avg_word_length", 0.0))
    words = float(feats.get("word_count", 0.0))
    sentence_count = float(feats.get("sentence_count", 0.0))

    if flesch >= 80:
        base = 9.0
    elif flesch >= 70:
        base = 8.0
    elif flesch >= 60:
        base = 7.5
    elif flesch >= 50:
        base = 6.0
    elif flesch >= 40:
        base = 4.5
    elif flesch >= 30:
        base = 3.0
    else:
        base = 1.5

    if words < 5:
        base = min(base, 3.0)
    elif words < 10:
        base = min(base, 5.0)

    if avg_word_len > 7.0:
        base -= 1.5
    elif avg_word_len > 6.0:
        base -= 0.5

    if sentence_count >= 3:
        base = min(base + 0.5, 10.0)

    return round(min(10.0, max(0.0, base)), 1)


def _score_sentiment_to_scale(sent):
    """Convert sentiment probabilities to 0-10 scale (MATCHING NOTEBOOK)."""
    pos = float(sent.get('positive', 0.0))
    neg = float(sent.get('negative', 0.0))
    neu = float(sent.get('neutral', 0.0))
    composite = pos - neg
    base = 5.0 + composite * 4.0
    if pos > 0.85:
        base += 0.5
    if neg > 0.85:
        base -= 0.5
    if neu > 0.70:
        base -= 0.5
    return round(min(10.0, max(0.0, float(base))), 1)


def _score_sentiment(raw_text):
    """
    Score sentiment using the pretrained transformer model (cardiffnlp/twitter-roberta-base-sentiment-latest).
    
    ONLY uses the transformer model - no TextBlob fallback.
    TextBlob was found to be ineffective (showed 0% label agreement and constant neutral scores in testing).
    
    Returns neutral sentiment if transformer fails to load or process.
    """
    text = (raw_text or "").strip()
    if not text:
        return {
            "label": "neutral",
            "positive": 0.0,
            "neutral": 1.0,
            "negative": 0.0,
            "sentiment_score": 0.0,
        }

    # Load transformer model (required, no fallback)
    if not _ensure_sentiment_model_loaded():
        # Model failed to load - warn and return neutral default
        try:
            warnings.warn(
                'Transformer sentiment model (cardiffnlp/twitter-roberta-base-sentiment-latest) could not be loaded. '
                'Ensure the model is downloaded and available. Returning neutral sentiment.',
                UserWarning,
            )
        except Exception:
            pass
        return {
            'label': 'neutral',
            'positive': 0.0,
            'neutral': 1.0,
            'negative': 0.0,
            'sentiment_score': 0.0,
        }

    try:
        inputs = _sent_tokenizer(text, return_tensors='pt', truncation=True)
        if torch is not None and torch.cuda.is_available():
            inputs = {k: v.to(_sent_model.device) for k, v in inputs.items()}
        with torch.no_grad() if torch is not None else dummy_context():
            outputs = _sent_model(**inputs)
        logits = outputs.logits if hasattr(outputs, 'logits') else None
        if logits is None:
            raise RuntimeError('no logits from sentiment model')
        
        # Convert logits to probabilities
        probs = None
        try:
            probs = torch.softmax(logits, dim=-1).cpu().numpy().flatten()
        except Exception:
            if np is not None:
                arr = np.array(logits.tolist()).flatten()
                exps = np.exp(arr - np.max(arr))
                probs = (exps / exps.sum()).astype(float)
            else:
                probs = [0.0] * logits.shape[-1]

        # Map probabilities to labels
        label_map = _sent_label_map
        if label_map is None:
            label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}

        prob_map = {}
        for i, p in enumerate(probs):
            name = label_map.get(i, str(i)).lower()
            if 'neg' in name:
                prob_map['negative'] = float(p)
            elif 'neu' in name:
                prob_map['neutral'] = float(p)
            elif 'pos' in name:
                prob_map['positive'] = float(p)
            else:
                prob_map[name] = float(p)

        negative = float(prob_map.get('negative', 0.0))
        neutral = float(prob_map.get('neutral', 0.0))
        positive = float(prob_map.get('positive', 0.0))
        sentiment_score = positive - negative
        
        # Determine label from composite score
        if sentiment_score >= 0.25:
            label = 'positive'
        elif sentiment_score <= -0.25:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'positive': round(positive, 3),
            'neutral': round(neutral, 3),
            'negative': round(negative, 3),
            'sentiment_score': round(float(sentiment_score), 3),
        }
    except Exception as e:
        # If transformer fails, return neutral instead of TextBlob
        return {
            'label': 'neutral',
            'positive': 0.0,
            'neutral': 1.0,
            'negative': 0.0,
            'sentiment_score': 0.0,
        }


class dummy_context:
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc, tb):
        return False


def _score_structure(feats, platform='instagram', benchmarks=None):
    benchmarks = benchmarks or {}
    platform = (platform or 'instagram').lower()
    b = benchmarks.get(platform, benchmarks.get('instagram', {}))
    cap = b.get('caption_length', {'optimal_min': 100, 'optimal_max': 180, 'max_allowed': 2200})
    ch = float(feats.get('char_count', 0))
    s = 5.0

    if cap['optimal_min'] <= ch <= cap['optimal_max']:
        s += 2.0
    elif ch < cap['optimal_min'] * 0.3:
        s -= 3.0
    elif ch < cap['optimal_min'] * 0.7:
        s -= 1.0
    elif ch < cap['optimal_min']:
        s += 0.5
    elif ch > cap['max_allowed']:
        s -= 3.0
    elif ch > cap['optimal_max'] * 2:
        s -= 1.0

    if feats.get('has_cta', 0.0) == 1.0:
        s += 1.5
    else:
        s -= 1.5

    caps_ratio = float(feats.get('caps_ratio', 0.0))
    exclaim_count = float(feats.get('exclaim_count', 0.0))
    if caps_ratio > 0.5:
        s -= 3.5
    elif caps_ratio > 0.3:
        s -= 2.0
    elif caps_ratio > 0.15 and exclaim_count >= 3:
        s -= 1.5

    if exclaim_count >= 4:
        s -= 1.0
    if float(feats.get('question_count', 0.0)) > 0:
        s += 0.5

    emoji_count = float(feats.get('emoji_count', 0.0))
    if 1 <= emoji_count <= 5:
        s += 0.5
    elif emoji_count > 15:
        s -= 1.0

    return round(min(10.0, max(0.0, float(s))), 1)


def _score_hashtags(feats, platform='instagram', benchmarks=None):
    benchmarks = benchmarks or {}
    platform = (platform or 'instagram').lower()
    b = benchmarks.get(platform, benchmarks.get('instagram', {}))
    ht = b.get('hashtag_count', {'optimal_min': 3, 'optimal_max': 7, 'spam_threshold': 20, 'max_allowed': 30})
    count = float(feats.get('hashtag_count', 0.0))

    # If no hashtags exist, treat as 0 per user preference "anything non existing is 0"
    if count == 0:
        s = 0.0
    elif ht['optimal_min'] <= count <= ht['optimal_max']:
        s = 9.0
    elif count < ht['optimal_min']:
        s = 6.0 + 0.5 * count
    elif count <= ht['spam_threshold']:
        s = max(3.0, 8.0 - (count - ht['optimal_max']) * 0.5)
    else:
        s = 1.5

    uniq_ratio = float(feats.get('unique_hashtag_ratio', 1.0))
    # Apply uniqueness penalty only when hashtags actually exist.
    if count > 0 and uniq_ratio < 0.7:
        s -= 1.0
    return round(min(10.0, max(0.0, float(s))), 1)


def _score_target_match(caption_text, feats, sent, startup_profile):
    if not startup_profile:
        return None

    caption = (caption_text or "").lower()
    keywords = startup_profile.get('keywords', []) or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]

    keyword_hits = sum(1 for keyword in keywords if keyword.lower() in caption)
    keyword_score = min(10.0, (keyword_hits / max(1, len(keywords))) * 10.0)

    target_len_min = float(startup_profile.get('target_len_min', 0) or 0)
    target_len_max = float(startup_profile.get('target_len_max', 10_000) or 10_000)
    char_count = float(feats.get('char_count', 0.0))
    if target_len_min <= char_count <= target_len_max:
        length_score = 10.0
    else:
        distance = min(abs(char_count - target_len_min), abs(char_count - target_len_max))
        length_score = max(0.0, 10.0 - distance / 25.0)

    preferred_sentiment = str(startup_profile.get('preferred_sentiment', 'neutral')).lower()
    sentiment_val = float(sent.get('sentiment_score', 0.0))
    if preferred_sentiment == 'positive':
        sentiment_score = max(0.0, 10.0 - abs(0.6 - sentiment_val) * 10.0)
    elif preferred_sentiment == 'negative':
        sentiment_score = max(0.0, 10.0 - abs(-0.4 - sentiment_val) * 10.0)
    else:
        sentiment_score = max(0.0, 10.0 - abs(sentiment_val) * 6.0)

    return round((keyword_score + length_score + sentiment_score) / 3.0, 1)


def evaluate_text(caption, platform='instagram', hashtags_separate=None, startup_profile=None, outputs_dir=None):
    """
    Notebook-aligned text evaluation for a caption or OCR-extracted text.
    
    Matches the notebook's evaluate_text() function with:
    - 3 dimensions: sentiment, structure, hashtags (readability removed by request)
    - Platform-specific weights
    - Data-driven target matching
    - Hard penalties for bad/spam posts
    - Major failures capping
    """
    outputs_dir = outputs_dir or DEFAULT_OUTPUTS_DIR
    artifacts = load_text_module_artifacts(outputs_dir)
    benchmarks = artifacts.get('benchmarks', {})
    module_config = artifacts.get('module_config', {})
    
    # If the notebook exported a local sentiment model path, prefer loading it first
    try:
        sent_cfg_path = module_config.get('sentiment_model') or module_config.get('sentiment_model_path')
        if sent_cfg_path:
            _ensure_sentiment_model_loaded(model_name=sent_cfg_path)
    except Exception:
        pass
    
    weights = module_config.get('dimension_weights', {})
    
    # Add hashtags_separate to the text if provided
    text = str(caption or '').strip()
    if hashtags_separate:
        text += ' ' + str(hashtags_separate).strip()
    
    # Extract all features
    feats = _extract_text_metrics(text)
    sent = _score_sentiment(text)
    
    # Get the benchmark for this platform
    platform_key = (platform or 'instagram').lower()
    bench = benchmarks.get(platform_key, benchmarks.get('instagram', {}))
    
    # Score dimensions (readability EXCLUDED by request)
    sentiment_score = _score_sentiment_to_scale(sent)  # Returns 0-10
    structure_score = _score_structure(feats, platform=platform, benchmarks=benchmarks)
    hashtags_score = _score_hashtags(feats, platform=platform, benchmarks=benchmarks)
    
    # Build dimension scores dict (readability excluded)
    dims = {
        'sentiment': sentiment_score,
        'structure': structure_score,
        'hashtags': hashtags_score,
    }
    
    # Get platform-specific weights (MATCHING NOTEBOOK)
    w = weights.get(
        platform_key,
        weights.get('instagram', {'sentiment': 0.25, 'structure': 0.25, 'hashtags': 0.30}),
    )
    
    # Calculate universal score using platform weights (only sum dimensions that exist)
    universal_score = round(sum(dims.get(d, 0.0) * float(w.get(d, 0.0)) for d in w), 2)
    
    # Calculate target match if profile provided
    target_match_score = _score_target_match(text, feats, sent, startup_profile)
    
    # If target_match exists, use equal weighting across ALL dimensions (MATCHING NOTEBOOK)
    if target_match_score is not None:
        dims['target_match'] = target_match_score
        overall = round(float(np.mean(list(dims.values()))), 2) if np else universal_score
    else:
        overall = universal_score
    
    # Build issues dict (MATCHING NOTEBOOK)
    cap_range = bench.get('caption_length', {'optimal_min': 100, 'optimal_max': 180, 'max_allowed': 2200})
    ht_range = bench.get('hashtag_count', {'optimal_min': 3, 'optimal_max': 7, 'spam_threshold': 20})
    
    issues = {
        'too_short': feats['char_count'] < cap_range['optimal_min'],
        'too_long': feats['char_count'] > cap_range['max_allowed'],
        'no_cta': feats['has_cta'] == 0.0,
        'no_hashtags': feats['hashtag_count'] == 0.0,
        'hashtag_spam': feats['hashtag_count'] >= ht_range['spam_threshold'],
        'all_caps': feats['caps_ratio'] > 0.3,
        'hard_to_read': feats['readability_flesch'] < 50,
        'negative_tone': sent['negative'] > 0.5,
        'flat_neutral': sent['neutral'] > 0.65 and feats['exclaim_count'] == 0.0,
    }
    
    # Apply hard penalties separately so the user can see the feature-based score
    # and the penalty impact independently.
    penalty = 0.0
    if issues['hashtag_spam']:
        penalty += 2.5
    if issues['all_caps']:
        penalty += 2.0
    if issues['no_cta']:
        penalty += 1.0
    if issues['too_short'] or issues['too_long']:
        penalty += 1.5
    if issues['hard_to_read']:
        penalty += 1.0
    
    raw_overall = round(float(overall), 2)
    penalized_overall = round(max(0.0, raw_overall - penalty), 2)
    
    # Major failures capping (MATCHING NOTEBOOK)
    major_failures = sum([
        issues['hashtag_spam'],
        issues['all_caps'],
        issues['too_short'],
        issues['too_long'],
    ])
    if major_failures >= 2 and penalized_overall > 4.5:
        penalized_overall = 4.5
    
    return {
        'overall_score': float(raw_overall),
        'penalized_overall_score': float(penalized_overall),
        'universal_score': float(universal_score),
        'dimension_scores': dims,
        'target_match_score': target_match_score,
        'startup_profile': startup_profile,
        'sentiment_detail': sent,
        'text_features': feats,
        'platform': platform_key,
        'issues': issues,
        'penalty_applied': round(float(penalty), 2),
    }


if __name__ == "__main__":
    print("text_inference helpers. Use extract_text_from_image(), evaluate_text_features(), and evaluate_text().")
