import json
import math
import os
from datetime import datetime

import joblib
import numpy as np

from text_inference import (
    evaluate_text,
    evaluate_text_features,
    extract_text_from_image,
    extract_text_regions_from_image,
)
from text_xai_inference import generate_text_xai_report
from visual_inference import extract_largest_rect_image, extract_visual_regions_from_image, predict_aesthetic
from xai_inference import generate_xai_report


def _normalize(text):
    return ' '.join((text or '').lower().split())


def _empty_region_map():
    return {
        'full_text': '',
        'top': '',
        'middle': '',
        'bottom': '',
        'left': '',
        'center': '',
        'right': '',
    }


def score_text_quality(text_feats):
    text = (text_feats or {}).get('raw_text', '')
    word_count = float((text_feats or {}).get('word_count', 0))
    sentiment = float((text_feats or {}).get('sentiment_polarity', 0.0))
    hashtag_count = float((text_feats or {}).get('hashtag_count', 0))
    mention_count = float((text_feats or {}).get('mention_count', 0))

    word_score = min(word_count / 40.0, 1.0) * 3.0
    sentiment_score = ((sentiment + 1.0) / 2.0) * 2.5
    cta_score = 1.5 if any(w in text.lower() for w in ['buy', 'link', 'click', 'subscribe', 'swipe', 'dm', 'shop', 'book', 'reserve']) else 0.0
    social_signal_score = min(hashtag_count, 3.0) * 0.4 + min(mention_count, 3.0) * 0.2

    score = max(0.0, min(10.0, word_score + sentiment_score + cta_score + social_signal_score))
    label = 'strong' if score >= 7.0 else 'moderate' if score >= 4.5 else 'weak'
    return {'score_0_10': float(score), 'class_label': label}


def combine_overall_evaluation(text_score, visual_score):
    overall_score = (0.45 * float(text_score)) + (0.55 * float(visual_score))
    overall_score = max(0.0, min(10.0, overall_score))
    label = 'high' if overall_score >= 6.0 else 'low'
    confidence = 0.5 + min(abs(overall_score - 5.0) / 10.0, 0.49)
    return {
        'overall_score_0_10': float(overall_score),
        'engagement_label': label,
        'engagement_confidence': float(confidence),
        'decision_threshold': 6.0,
    }


def load_engagement_model(outputs_dir):
    model_path = os.path.join(outputs_dir, 'engagement_model.pkl')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f'engagement_model.pkl not found in {outputs_dir}')

    model = joblib.load(model_path)
    le_path = os.path.join(outputs_dir, 'engagement_label_encoder.pkl')
    scaler_path = os.path.join(outputs_dir, 'text_scaler.pkl')
    enc_path = os.path.join(outputs_dir, 'text_encoders.pkl')

    return {
        'model': model,
        'label_encoder': joblib.load(le_path) if os.path.exists(le_path) else None,
        'scaler': joblib.load(scaler_path) if os.path.exists(scaler_path) else None,
        'encoders': joblib.load(enc_path) if os.path.exists(enc_path) else None,
    }


def build_feature_vector(text_feats, visual_feats, metadata=None, outputs_dir=None):
    feats = {
        'text_word_count': float((text_feats or {}).get('word_count', 0)),
        'text_char_count': float((text_feats or {}).get('char_count', 0)),
        'text_hashtag_count': float((text_feats or {}).get('hashtag_count', 0)),
        'text_sentiment': float((text_feats or {}).get('sentiment_polarity', 0.0)),
        'image_score_0_10': float((visual_feats or {}).get('score_0_10', 0.0)),
        'image_confidence': float((visual_feats or {}).get('confidence', 0.0)),
    }

    metadata = metadata if isinstance(metadata, dict) else {}
    feats['has_metadata_platform'] = 1.0 if metadata.get('platform') else 0.0

    columns = list(feats.keys())
    vector = [feats[column] for column in columns]
    return np.array(vector, dtype=float).reshape(1, -1), columns


def predict_engagement_from_screenshot(
    screenshot_path,
    outputs_dir,
    metadata=None,
    do_extract_image=True,
    include_legacy_model=False,
):
    """Full pipeline: screenshot -> text extraction -> image crop -> visual eval -> engagement prediction."""
    text_regions = _empty_region_map()
    try:
        text_regions = extract_text_regions_from_image(screenshot_path)
        text = text_regions.get('full_text') or extract_text_from_image(screenshot_path)
    except Exception:
        text = ''

    platform_override = (metadata or {}).get('platform') if isinstance(metadata, dict) else None
    startup_profile = metadata if isinstance(metadata, dict) else None

    # Automatic platform detection has been disabled per user request.
    # Use explicit metadata override when provided; otherwise mark platform as unknown.
    if platform_override and str(platform_override).strip().lower() not in {'auto', 'detect', 'automatic', ''}:
        platform = str(platform_override).lower()
        platform_source = 'metadata_override'
    else:
        platform = 'unknown'
        platform_source = 'none'

    text_eval = evaluate_text(text, platform=platform, startup_profile=startup_profile, outputs_dir=outputs_dir)
    text_feats = text_eval.get('feature_values', evaluate_text_features(text))

    try:
        text_xai = generate_text_xai_report(raw_text=text, platform=platform, outputs_dir=outputs_dir, eval_result=text_eval)
    except Exception as exc:
        text_xai = {'report_error': str(exc), 'raw_text_full': text, 'raw_text_preview': text[:500]}

    try:
        image_path = extract_largest_rect_image(screenshot_path) if do_extract_image else screenshot_path
    except Exception:
        image_path = screenshot_path

    try:
        visual_feats = predict_aesthetic(
            image_path=image_path,
            raw_attrs_dict=None,
            outputs_dir=outputs_dir,
            use_tta=True,
        )
    except Exception as exc:
        raise RuntimeError(
            'Could not run the notebook-trained visual scorer. The final screenshot evaluation requires the saved model artifacts in outputs/.'
        ) from exc

    visual_score = float(visual_feats.get('score_0_10', 0.0))

    try:
        visual_xai = generate_xai_report(
            image_path,
            raw_attrs_dict=None,
            outputs_dir=outputs_dir,
            actual_visual_score=visual_score,
            visual_eval_result=visual_feats,
        )
    except Exception as exc:
        visual_xai = {'report_error': str(exc)}

    # Encode the extracted image to base64 for display
    extracted_image_b64 = None
    try:
        import base64
        with open(image_path, 'rb') as f:
            extracted_image_b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"[Pipeline] Could not encode extracted image: {e}")

    overall_eval = combine_overall_evaluation(text_eval['overall_score'], visual_score)
    fv, cols = build_feature_vector(text_feats, visual_feats, metadata=metadata, outputs_dir=outputs_dir)

    result = {
        'extracted_text': text,
        'ocr_regions': text_regions,
        'platform_used_for_text_evaluation': platform,
        'text_features': text_feats,
        'text_evaluation': text_eval,
        'text_xai': text_xai,
        'visual_features': visual_feats,
        'visual_xai': visual_xai,
        'extracted_image_b64': extracted_image_b64,
        'overall_evaluation': overall_eval,
        'feature_columns': cols,
        'engagement_pred_raw': 1.0 if overall_eval['engagement_label'] == 'high' else 0.0,
        'engagement_confidence': overall_eval['engagement_confidence'],
    }

    if include_legacy_model:
        try:
            artifacts = load_engagement_model(outputs_dir)
            model = artifacts['model']
            pred = model.predict(fv)
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(fv).max(axis=1)[0]
            else:
                proba = float(0.0)
            result['legacy_model_pred_raw'] = float(pred[0])
            result['legacy_model_confidence'] = float(proba)
        except Exception as exc:
            result['legacy_model_error'] = str(exc)

    return result


if __name__ == '__main__':
    print('Run predict_engagement_from_screenshot(screenshot_path, outputs_dir)')


def run_demo(screenshot_path=None, outputs_dir=None, metadata=None):
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)

    if not screenshot_path:
        try:
            screenshot_path = input('Enter the full path to your screenshot: ').strip()
        except Exception as exc:
            raise ValueError('A screenshot path is required to run the demo.') from exc

    if not screenshot_path or not os.path.exists(screenshot_path):
        raise FileNotFoundError(f'Screenshot not found: {screenshot_path}')

    res = predict_engagement_from_screenshot(screenshot_path, outputs_dir, metadata=metadata)

    out_path = os.path.join(outputs_dir, 'pipeline_demo_output.json')
    with open(out_path, 'w', encoding='utf-8') as fj:
        json.dump(res, fj, indent=2, ensure_ascii=False)

    return res
