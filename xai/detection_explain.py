"""XAI utilities for signature detection: confidence explanation and focus regions."""
from typing import List, Dict, Any


def detection_explanation_text(detections: List[Dict[str, Any]]) -> str:
    """Generate readable explanation of signature detections."""
    if not detections:
        return "No signatures detected in the image."
    
    total = len(detections)
    high_conf = [d for d in detections if d.get('confidence', 0) >= 0.7]
    low_conf = [d for d in detections if d.get('confidence', 0) < 0.7]
    
    avg_conf = sum(d.get('confidence', 0) for d in detections) / total if total else 0
    
    text = f"Detected {total} signature region{'s' if total > 1 else ''}. "
    text += f"High confidence: {len(high_conf)}, Low confidence: {len(low_conf)}. "
    text += f"Average confidence: {avg_conf:.1%}. "
    
    if high_conf:
        text += "High-confidence detections are likely actual signatures."
    if low_conf:
        text += f" {len(low_conf)} region{'s' if len(low_conf) > 1 else ''} may not be signatures."
    
    return text


def detection_focus_regions(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return focus regions (bboxes) with confidence scores for visualization."""
    regions = []
    for det in detections:
        box = det.get('box_xyxy', [0, 0, 1, 1])
        conf = det.get('confidence', 0.0)
        regions.append({
            'box_norm_xyxy': box,
            'confidence': conf,
            'class': det.get('class_name', 'signature'),
        })
    return regions
