"""Text XAI (Explainability) for engagement prediction.

Provides:
- Feature importance: which text metrics matter most (word count, sentiment, structure, hashtags, etc.)
- Dimension breakdown: contribution of each scoring dimension (sentiment, structure, hashtags)
- Issue flagging: explicit problems detected (low readability, weak CTA, caps-heavy, etc.)
- Interpretation: natural language explanation of why text got this score
"""

import json
import os
from PIL import Image
import numpy as np
from text_inference import (
    extract_text_from_image,
    evaluate_text,
    _extract_text_metrics,
    load_text_module_artifacts,
)


def analyze_text_features(raw_text, platform='instagram', outputs_dir=None):
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')

    artifacts = load_text_module_artifacts(outputs_dir)
    module_config = artifacts.get('module_config', {})

    artifacts = load_text_module_artifacts(outputs_dir)
    module_config = artifacts.get('module_config', {})
    
    # Extract metrics
    feats = _extract_text_metrics(raw_text)
    
    # Feature importance heuristic: score impact if feature is absent/low
    feature_importance = {
        'word_count': {
            'value': float(feats.get('word_count', 0)),
            'impact': 'Word count (optimal: 10-150 words)',
            'importance': 0.15,
        },
        'char_count': {
            'value': float(feats.get('char_count', 0)),
            'impact': 'Character count (optimal: 100-2200)',
            'importance': 0.15,
        },
        'hashtag_count': {
            'value': float(feats.get('hashtag_count', 0)),
            'impact': 'Hashtag count (optimal: 3-7 for Instagram)',
            'importance': 0.15,
        },
        'has_cta': {
            'value': float(feats.get('has_cta', 0)),
            'impact': 'Call-to-action present (binary: buy, click, link, etc.)',
            'importance': 0.10,
        },
        'sentiment_polarity': {
            'value': float(feats.get('avg_word_length', 0.0)),
            'impact': 'Average word length (shorter=more readable)',
            'importance': 0.10,
        },
        'emoji_count': {
            'value': float(feats.get('emoji_count', 0)),
            'impact': 'Emoji count (1-5 optimal)',
            'importance': 0.05,
        },
        'caps_ratio': {
            'value': float(feats.get('caps_ratio', 0.0)),
            'impact': 'CAPS ratio (lower=better, <15% optimal)',
            'importance': 0.05,
        },
    }
    
    return {
        'raw_text': raw_text,
        'feature_metrics': feats,
        'feature_importance': feature_importance,
    }


def analyze_dimension_contribution(eval_result, dimension_weights=None):
    """
    Break down how each dimension (readability, sentiment, structure, hashtags)
    contributed to the overall text score.
    
    Args:
        eval_result: output from evaluate_text()
        
    Returns:
        dict with dimension contributions and interpretations
    """
    dimension_scores = eval_result.get('dimension_scores', {})
    overall_score = eval_result.get('overall_score', 0.0)
    
    # Use notebook weights when available; fall back to a neutral default.
    dimension_weights = dimension_weights or {
        'readability': 0.25,
        'sentiment': 0.25,
        'structure': 0.25,
        'hashtags': 0.25,
    }
    
    # Calculate weighted contribution
    dimension_contribution = {}
    total_weighted = 0.0
    
    for dim, score in dimension_scores.items():
        weight = dimension_weights.get(dim, 0.25)
        contribution = score * weight
        dimension_contribution[dim] = {
            'score': float(score),
            'weight': weight,
            'contribution': float(contribution),
        }
        total_weighted += contribution
    
    # Normalize to show % contribution
    for dim in dimension_contribution:
        if total_weighted > 0:
            pct = (dimension_contribution[dim]['contribution'] / total_weighted) * 100
        else:
            pct = 0.0
        dimension_contribution[dim]['percent_of_total'] = float(pct)
    
    # Rank by contribution
    ranked = sorted(
        dimension_contribution.items(),
        key=lambda x: x[1]['contribution'],
        reverse=True,
    )
    
    return {
        'dimension_contribution': dimension_contribution,
        'ranked_by_contribution': ranked,
        'total_weighted_score': float(total_weighted),
        'applied_penalty': float(eval_result.get('penalty_applied', 0.0)),
        'universal_score': float(eval_result.get('universal_score', total_weighted)),
        'final_score': float(eval_result.get('overall_score', 0.0)),
    }


def interpret_text_score(eval_result, feature_analysis=None):
    """
    Generate natural language interpretation of why text got this score.
    
    Args:
        eval_result: output from evaluate_text()
        feature_analysis: optional output from analyze_text_features()
        
    Returns:
        str with interpretation
    """
    score = eval_result.get('overall_score', 0.0)
    label = eval_result.get('overall_label', 'unknown')
    dimension_scores = eval_result.get('dimension_scores', {})
    issues = eval_result.get('issues', {})
    
    interpretation_parts = []
    
    # Overall assessment
    if score >= 6.5:
        interpretation_parts.append(f"Strong engagement potential (score {score:.1f}/10).")
    elif score >= 4.5:
        interpretation_parts.append(f"Moderate engagement (score {score:.1f}/10).")
    else:
        interpretation_parts.append(f"Low engagement risk (score {score:.1f}/10).")
    
    # Dimension strengths
    strong_dims = [d for d, s in dimension_scores.items() if s >= 7.0]
    weak_dims = [d for d, s in dimension_scores.items() if s <= 4.0]
    
    if strong_dims:
        interpretation_parts.append(f"Strengths: {', '.join(strong_dims)}.")
    
    if weak_dims:
        interpretation_parts.append(f"Weaknesses: {', '.join(weak_dims)}.")
    
    # Issues
    flagged_issues = [k.replace('_', ' ').title() for k, v in issues.items() if v]
    if flagged_issues:
        interpretation_parts.append(f"Issues detected: {', '.join(flagged_issues)}.")
    
    # Recommendations
    recommendations = []
    if issues.get('low_readability'):
        recommendations.append("Simplify text (lower Flesch score)")
    if issues.get('weak_cta'):
        recommendations.append("Add call-to-action (click, link, subscribe, etc.)")
    if issues.get('too_short'):
        recommendations.append("Expand caption to 100+ characters")
    if issues.get('too_long'):
        recommendations.append("Trim to under 2200 characters")
    if issues.get('caps_heavy'):
        recommendations.append("Reduce CAPS emphasis")
    
    if recommendations:
        interpretation_parts.append(f"Recommendations: {'; '.join(recommendations)}.")
    
    return " ".join(interpretation_parts)


def analyze_image_composition(image_path):
    """
    Analyze image composition: dimensions, colors, brightness, contrast.
    
    Args:
        image_path: path to image
        
    Returns:
        dict with image composition details
    """
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Basic properties
    composition = {
        "file_path": image_path,
        "dimensions": {"width": img.width, "height": img.height},
        "aspect_ratio": round(img.width / img.height, 2),
        "color_space": img.mode,
        "file_size_kb": round(os.path.getsize(image_path) / 1024, 1),
    }
    
    # Color analysis (RGB channels)
    if img.mode in ['RGB', 'RGBA']:
        if img.mode == 'RGBA':
            img_rgb = img.convert('RGB')
            img_array = np.array(img_rgb)
        
        r_mean = float(img_array[:, :, 0].mean())
        g_mean = float(img_array[:, :, 1].mean())
        b_mean = float(img_array[:, :, 2].mean())
        
        composition["average_color"] = {
            "red": round(r_mean, 1),
            "green": round(g_mean, 1),
            "blue": round(b_mean, 1),
        }
        
        # Brightness (luminance)
        luminance = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        brightness = float(luminance.mean())
        composition["brightness_0_255"] = round(brightness, 1)
        composition["brightness_label"] = (
            "dark" if brightness < 85 else "medium" if brightness < 170 else "bright"
        )
        
        # Contrast (std dev of luminance)
        contrast = float(luminance.std())
        composition["contrast_std"] = round(contrast, 1)
        composition["contrast_label"] = (
            "low" if contrast < 30 else "medium" if contrast < 70 else "high"
        )
        
        # Color saturation
        max_channel = np.maximum(np.maximum(img_array[:, :, 0], img_array[:, :, 1]), img_array[:, :, 2])
        min_channel = np.minimum(np.minimum(img_array[:, :, 0], img_array[:, :, 1]), img_array[:, :, 2])
        saturation = (max_channel - min_channel).mean() / 255.0
        composition["color_saturation_0_1"] = round(saturation, 3)
        composition["saturation_label"] = (
            "desaturated" if saturation < 0.2 else "normal" if saturation < 0.5 else "vibrant"
        )
    
    return composition


def generate_text_xai_report(image_path=None, raw_text=None, platform='instagram', outputs_dir=None, eval_result=None):
    """
    Generate full XAI report for text evaluation.
    
    Args:
        image_path: optional path to image (will OCR if provided)
        raw_text: optional raw text (use instead of image OCR)
        platform: 'instagram', 'linkedin', 'twitter', 'facebook'
        outputs_dir: model artifacts directory
        
    Returns:
        dict with full XAI report
    """
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')

    artifacts = load_text_module_artifacts(outputs_dir)
    module_config = artifacts.get('module_config', {})
    
    # Extract text
    if raw_text is None:
        if image_path is None:
            raise ValueError("Must provide either image_path or raw_text")
        raw_text = extract_text_from_image(image_path)
    
    # Evaluate text only if the pipeline did not already compute it.
    if eval_result is None:
        eval_result = evaluate_text(raw_text, platform=platform, outputs_dir=outputs_dir)
    
    # Feature analysis
    feature_analysis = analyze_text_features(raw_text, platform, outputs_dir)
    
    # Dimension contribution
    dimension_analysis = analyze_dimension_contribution(
        eval_result,
        dimension_weights=module_config.get('dimension_weights'),
    )
    
    # Interpretation
    interpretation = interpret_text_score(eval_result, feature_analysis)
    
    # Image composition (if image provided)
    composition = None
    if image_path:
        composition = analyze_image_composition(image_path)
    
    # Assemble report
    report = {
        'source': 'image_ocr' if image_path else 'raw_text',
        'image_path': image_path,
        'image_composition': composition,
        'raw_text_full': raw_text,  # Full text without truncation
        'raw_text_preview': raw_text[:500] + ('...' if len(raw_text) > 500 else ''),  # for quick preview
        'text_length': len(raw_text),
        'platform': platform,
        'overall_score': eval_result.get('overall_score', 0.0),
        'penalized_overall_score': eval_result.get('penalized_overall_score', eval_result.get('overall_score', 0.0)),
        'universal_score': eval_result.get('universal_score', 0.0),
        'penalty_applied': eval_result.get('penalty_applied', 0.0),
        'overall_label': eval_result.get('overall_label', 'unknown'),
        'dimension_scores': eval_result.get('dimension_scores', {}),
        'dimension_contribution': dimension_analysis['dimension_contribution'],
        'ranked_dimensions': [
            {
                'dimension': dim,
                'score': scores['score'],
                'contribution_percent': scores['percent_of_total'],
            }
            for dim, scores in dimension_analysis['ranked_by_contribution']
        ],
        'feature_metrics': feature_analysis['feature_metrics'],
        'top_features': {
            k: v for k, v in list(
                sorted(
                    feature_analysis['feature_importance'].items(),
                    key=lambda x: x[1]['importance'],
                    reverse=True,
                )[:5]
            )
        },
        'issues_detected': eval_result.get('issues', {}),
        'interpretation': interpretation,
    }
    
    # Save report
    report_path = os.path.join(outputs_dir, 'text_xai_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return {**report, 'report_save_path': report_path}


if __name__ == "__main__":
    print("Text XAI inference module for engagement prediction.")
