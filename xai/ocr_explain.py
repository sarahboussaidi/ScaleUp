"""XAI utilities for OCR: confidence heatmaps and text region explanations."""
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Dict, Any


def ocr_confidence_heatmap(img_pil, ocr_results: List[Dict[str, Any]]) -> np.ndarray:
    """Create a confidence heatmap for OCR results.
    
    Args:
        img_pil: PIL Image
        ocr_results: list of dicts with 'box' (x,y,w,h) and 'conf' keys
    
    Returns:
        Heatmap as numpy array (0..1)
    """
    w, h = img_pil.size
    heatmap = np.zeros((h, w), dtype=np.float32)
    
    for result in ocr_results:
        conf = result.get('conf', 0.5)
        box = result.get('box', [0, 0, 1, 1])
        x, y, bw, bh = box
        x1, y1 = int(x), int(y)
        x2, y2 = min(int(x + bw), w), min(int(y + bh), h)
        
        if x1 < x2 and y1 < y2:
            heatmap[y1:y2, x1:x2] = max(heatmap[y1:y2, x1:x2].max(), conf)
    
    return heatmap


def ocr_explanation_text(ocr_results: List[Dict[str, Any]]) -> str:
    """Generate a readable explanation of OCR confidence."""
    if not ocr_results:
        return "No text detected."
    
    high_conf = [r for r in ocr_results if r.get('conf', 0) >= 0.8]
    low_conf = [r for r in ocr_results if r.get('conf', 0) < 0.8]
    
    avg_conf = np.mean([r.get('conf', 0) for r in ocr_results])
    
    text = f"Detected {len(ocr_results)} text regions. "
    text += f"High confidence: {len(high_conf)}, Low confidence: {len(low_conf)}. "
    text += f"Average confidence: {avg_conf:.1%}. "
    
    if low_conf:
        text += f"Note: {len(low_conf)} regions have lower confidence and may be misread."
    
    return text


def draw_ocr_boxes(img_pil, ocr_results: List[Dict[str, Any]], confidence_threshold: float = 0.5):
    """Draw bounding boxes colored by confidence."""
    img = img_pil.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    
    for result in ocr_results:
        conf = result.get('conf', 0.5)
        box = result.get('box', [0, 0, 1, 1])
        text = result.get('text', '')
        
        x, y, bw, bh = box
        x1, y1, x2, y2 = int(x), int(y), int(x + bw), int(y + bh)
        
        # Color by confidence: red (low) -> yellow (mid) -> green (high)
        if conf >= 0.8:
            color = (0, 255, 0)
        elif conf >= 0.6:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        draw.text((x1, max(0, y1 - 15)), f"{text[:20]}", fill=color)
    
    return img
