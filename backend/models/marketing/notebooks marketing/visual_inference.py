import json
import math
import os

import numpy as np
from PIL import Image, ImageOps

try:
    import cv2
except Exception:
    cv2 = None

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
except Exception:
    torch = None
    nn = None
    models = None
    transforms = None


DEFAULT_CLASS_NAMES = ["bad", "average", "good"]
DEFAULT_ATTR_COLS = [
    "BalacingElements",
    "ColorHarmony",
    "Content",
    "DoF",
    "Light",
    "MotionBlur",
    "Object",
    "Repetition",
    "RuleOfThirds",
    "Symmetry",
    "VividColor",
]


def extract_largest_rect_image(screenshot_path, out_path=None, margin=0.04):
    """Crop the main content container from a social screenshot.

    The goal is to keep the full post area used for visual evaluation, not a
    single image fragment and not the whole page chrome/background.
    If OpenCV is unavailable or no good content box is found, the original image
    path is returned.
    """
    if cv2 is None:
        return screenshot_path

    img = cv2.imread(screenshot_path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {screenshot_path}")

    img_h, img_w = img.shape[:2]
    full_area = float(img_h * img_w)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _score_box(x, y, w, h, contour_area=None):
        bbox_area = float(max(1, w * h))
        area_ratio = bbox_area / full_area
        if area_ratio < 0.10 or area_ratio > 0.96:
            return None
        if w < 80 or h < 80:
            return None
        if x <= 1 and y <= 1 and (x + w) >= img_w - 1 and (y + h) >= img_h - 1:
            return None

        center_x = x + (w / 2.0)
        center_y = y + (h / 2.0)
        dx = abs((center_x / max(1.0, img_w)) - 0.5)
        dy = abs((center_y / max(1.0, img_h)) - 0.5)
        center_bias = 1.0 - min(1.0, (dx + dy) / 1.0)

        fill_ratio = 0.0
        if contour_area is not None:
            fill_ratio = float(contour_area) / bbox_area

        # Prefer large, well-filled, centered post-like panels.
        score = (1.8 * area_ratio) + (0.8 * min(1.0, fill_ratio)) + (0.4 * center_bias)
        return {
            "box": (x, y, w, h),
            "score": score,
            "area_ratio": area_ratio,
        }

    candidates = []

    # First pass: foreground mask against background using Otsu thresholding.
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    binary = cv2.dilate(binary, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)), iterations=1)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < max(800, int(full_area * 0.01)):
            continue
        x, y, w, h = cv2.boundingRect(contour)
        scored = _score_box(x, y, w, h, contour_area=contour_area)
        if scored is not None:
            candidates.append(scored)

    # Second pass: edge-based fallback for screenshots with light backgrounds.
    edged = cv2.Canny(blur, 30, 140)
    edged = cv2.dilate(edged, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)), iterations=2)
    edged = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < max(800, int(full_area * 0.01)):
            continue
        x, y, w, h = cv2.boundingRect(contour)
        scored = _score_box(x, y, w, h, contour_area=contour_area)
        if scored is not None:
            candidates.append(scored)

    if not candidates:
        return screenshot_path

    best = max(candidates, key=lambda item: item["score"])
    x, y, w, h = best["box"]

    pad_h = int(h * margin)
    pad_w = int(w * margin)
    x0 = max(0, x - pad_w)
    y0 = max(0, y - pad_h)
    x1 = min(img_w, x + w + pad_w)
    y1 = min(img_h, y + h + pad_h)

    crop = img[y0:y1, x0:x1]
    crop_area = float(crop.shape[0] * crop.shape[1]) if crop.size else 0.0
    crop_ratio = crop_area / full_area if full_area > 0 else 0.0

    # Reject crops that are clearly too tiny or effectively the whole page.
    if crop_ratio < 0.20 or crop_ratio > 0.95:
        return screenshot_path

    if out_path is None:
        base, ext = os.path.splitext(screenshot_path)
        out_path = f"{base}_crop{ext}"

    cv2.imwrite(out_path, crop)
    return out_path


class AestheticFusionModel(nn.Module):
    def __init__(self, num_classes=3, n_attrs=11):
        super().__init__()

        backbone = models.efficientnet_b2(weights=None)

        blocks = list(backbone.features.children())
        for i, block in enumerate(blocks):
            for param in block.parameters():
                param.requires_grad = (i >= 4)

        self.img_backbone = nn.Sequential(
            backbone.features,
            backbone.avgpool,
        )
        img_feat_dim = 1408

        self.attr_encoder = nn.Sequential(
            nn.Linear(n_attrs, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 64),
            nn.ReLU(),
        )

        self.img_neck = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(img_feat_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
        )

        self.fusion = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(512 + 64, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
        )

        self.cls_head = nn.Linear(128, num_classes)
        self.score_head = nn.Sequential(nn.Linear(128, 1), nn.Sigmoid())

    def forward(self, img, attrs):
        img_feat = self.img_backbone(img)
        img_feat = img_feat.view(img_feat.size(0), -1)
        img_feat = self.img_neck(img_feat)

        attr_feat = self.attr_encoder(attrs)
        fused = torch.cat([img_feat, attr_feat], dim=1)
        fused = self.fusion(fused)

        cls_logits = self.cls_head(fused)
        score = self.score_head(fused).squeeze(1)
        return cls_logits, score


def _resolve_device(device=None):
    if device is not None:
        return device
    if torch is None:
        raise ImportError("PyTorch is required for visual model inference.")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_visual_model(outputs_dir, device=None):
    """Load the trained EfficientNet-B2 visual fusion model and metadata."""
    device = _resolve_device(device)

    config_path = os.path.join(outputs_dir, "visual_model_config.json")
    model_path = os.path.join(outputs_dir, "visual_scorer_best.pth")
    stats_path = os.path.join(outputs_dir, "attr_norm_stats.json")

    missing = [path for path in [config_path, model_path, stats_path] if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(
            "Missing trained visual-model artifact(s): " + ", ".join(missing)
        )

    config = _load_json(config_path)
    norm_stats = _load_json(stats_path)

    attr_cols = config.get("attr_cols_orig", DEFAULT_ATTR_COLS)
    class_names = config.get("class_names", DEFAULT_CLASS_NAMES)
    n_attrs = int(config.get("n_attrs", len(attr_cols)))

    model = AestheticFusionModel(num_classes=len(class_names), n_attrs=n_attrs).to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    return {
        "model": model,
        "device": device,
        "config": config,
        "norm_stats": norm_stats,
        "attr_cols": attr_cols,
        "class_names": class_names,
    }


def normalize_attrs(raw_attrs_dict, norm_stats, attr_cols):
    normalized = []
    raw_attrs_dict = raw_attrs_dict or {}

    for col in attr_cols:
        raw_val = float(raw_attrs_dict.get(col, 0.0))
        cmin = float(norm_stats[col]["min"])
        cmax = float(norm_stats[col]["max"])
        norm_val = (raw_val - cmin) / (cmax - cmin + 1e-8)
        normalized.append(float(np.clip(norm_val, 0.0, 1.0)))

    return normalized


def _build_image_tensor(image, use_tta):
    if use_tta:
        crop_tf = transforms.Compose([
            transforms.Resize((288, 288)),
            transforms.FiveCrop(256),
            transforms.Lambda(lambda crops: torch.stack([
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(
                    transforms.ToTensor()(crop)
                ) for crop in crops
            ])),
        ])
        return crop_tf(image)

    base_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return base_tf(image).unsqueeze(0)


def detailed_feature_visual_score(image_path, outputs_dir=None):
    """Image-only detailed visual score based on interpretable feature proxies.

    This is stricter than the raw class head: it scores visual quality from
    composition, color harmony, contrast, symmetry, sharpness, and related cues.
    """
    image = ImageOps.exif_transpose(Image.open(image_path).convert("RGB")).resize((256, 256))
    rgb = np.asarray(image).astype(np.float32)
    rgb_u8 = rgb.astype(np.uint8)

    if cv2 is not None:
        gray = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2GRAY).astype(np.float32)
        hsv = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2HSV).astype(np.float32)
        hue = hsv[:, :, 0] / 180.0
    else:
        gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        hue = None

    def _clip01(value):
        return float(np.clip(value, 0.0, 1.0))

    def _score_target(value, target, tolerance):
        tolerance = max(float(tolerance), 1e-6)
        return float(10.0 * math.exp(-((float(value) - float(target)) ** 2) / (2.0 * tolerance * tolerance)))

    def _score_between(value, low, high):
        low = float(low)
        high = float(high)
        if high <= low:
            return 5.0
        norm = _clip01((float(value) - low) / (high - low))
        return float(10.0 * norm)

    def _entropy_score(values, bins=32):
        hist, _ = np.histogram(values, bins=bins, range=(float(values.min()), float(values.max()) + 1e-8))
        probs = hist.astype(np.float32)
        total = float(probs.sum())
        if total <= 0:
            return 0.0
        probs = probs / total
        probs = probs[probs > 0]
        entropy = -float(np.sum(probs * np.log(probs)))
        entropy /= float(math.log(max(2, bins)))
        return _clip01(entropy)

    def _normalize(arr):
        arr = arr.astype(np.float32)
        mn = float(arr.min())
        mx = float(arr.max())
        if mx - mn < 1e-8:
            return np.zeros_like(arr, dtype=np.float32)
        return (arr - mn) / (mx - mn)

    # Core image cues
    luminance = gray
    brightness = float(luminance.mean())
    contrast_std = float(luminance.std())
    saturation_map = rgb.max(axis=2) - rgb.min(axis=2)
    vividness = float(saturation_map.mean() / 255.0)

    gx = np.gradient(luminance, axis=1)
    gy = np.gradient(luminance, axis=0)
    grad_mag = np.hypot(gx, gy)
    edge_density = float((grad_mag > np.percentile(grad_mag, 75)).mean())
    sharpness = float(grad_mag.var())

    if cv2 is not None:
        laplacian = cv2.Laplacian(luminance.astype(np.float32), cv2.CV_32F)
        lap_var = float(laplacian.var())
        center_lap_var = float(laplacian[64:192, 64:192].var())
        border_mask = np.ones_like(luminance, dtype=bool)
        border_mask[64:192, 64:192] = False
        border_lap_var = float(laplacian[border_mask].var()) if np.any(border_mask) else lap_var
    else:
        lap_var = sharpness
        center_lap_var = lap_var
        border_lap_var = lap_var

    # Saliency proxy for composition cues
    saliency = 0.75 * _normalize(grad_mag) + 0.25 * _normalize(saturation_map)
    saliency_sum = float(saliency.sum()) + 1e-8
    yy, xx = np.mgrid[0:256, 0:256]
    cx = float((saliency * xx).sum() / saliency_sum) / 255.0
    cy = float((saliency * yy).sum() / saliency_sum) / 255.0

    left_mass = float(saliency[:, :128].sum() / saliency_sum)
    right_mass = float(saliency[:, 128:].sum() / saliency_sum)
    top_mass = float(saliency[:128, :].sum() / saliency_sum)
    bottom_mass = float(saliency[128:, :].sum() / saliency_sum)

    center = saliency[64:192, 64:192]
    center_mass = float(center.sum() / saliency_sum)

    # Tile regularity for repetition / structured pattern proxy
    tile_means = []
    for y0 in range(0, 256, 64):
        for x0 in range(0, 256, 64):
            tile_means.append(float(luminance[y0:y0 + 64, x0:x0 + 64].mean()))
    tile_means = np.asarray(tile_means, dtype=np.float32)
    tile_regularity = 1.0 - _clip01(float(tile_means.std()) / 64.0)

    # Color harmony proxy: palette coherence + hue concentration
    rgb_std = float(rgb.std(axis=2).mean() / 255.0)
    if hue is not None:
        hist, _ = np.histogram(hue, bins=12, range=(0.0, 1.0))
        hist = hist.astype(np.float32)
        hist_sum = float(hist.sum()) + 1e-8
        probs = hist / hist_sum
        probs = probs[probs > 0]
        hue_entropy = -float(np.sum(probs * np.log(probs))) / float(math.log(12))
        hue_coherence = 1.0 - _clip01(hue_entropy)
    else:
        hue_coherence = 1.0 - _clip01(rgb_std)
    color_harmony = 0.55 * hue_coherence + 0.45 * (1.0 - _clip01(rgb_std))

    # Feature scores on 0-10
    feature_scores = {
        "Content": round(float(0.55 * (10.0 * _entropy_score(luminance)) + 0.45 * _score_target(edge_density, 0.08, 0.05)), 2),
        "ColorHarmony": round(float(10.0 * _clip01(color_harmony)), 2),
        "Object": round(float(10.0 * _clip01(center_mass)), 2),
        "VividColor": round(float(_score_target(vividness, 0.45, 0.22)), 2),
        "Light": round(float(_score_target(brightness, 150.0, 65.0)), 2),
        # DoF is a sharpness proxy: good images often keep the subject sharper than the background.
        "DoF": round(float(max(0.0, min(10.0, (
            0.40 * _score_between(lap_var, 35.0, 220.0)
            + 0.35 * _score_target((center_lap_var + 1e-8) / (border_lap_var + 1e-8), 1.25, 0.35)
            + 0.25 * _score_target((float(grad_mag[64:192, 64:192].mean()) + 1e-8) / (float(grad_mag.mean()) + 1e-8), 1.05, 0.25)
        )))), 2),
        "RuleOfThirds": round(float(10.0 * math.exp(-((min(
            math.hypot(cx - 1.0 / 3.0, cy - 1.0 / 3.0),
            math.hypot(cx - 2.0 / 3.0, cy - 1.0 / 3.0),
            math.hypot(cx - 1.0 / 3.0, cy - 2.0 / 3.0),
            math.hypot(cx - 2.0 / 3.0, cy - 2.0 / 3.0)
        ) / 0.28) ** 2))), 2),
        "BalacingElements": round(float(10.0 * _clip01(1.0 - (abs(left_mass - right_mass) + abs(top_mass - bottom_mass)) / 2.0)), 2),
        "Repetition": round(float(10.0 * _clip01(tile_regularity)), 2),
        "MotionBlur": round(float(_score_between(lap_var, 20.0, 180.0)), 2),
        "Symmetry": round(float(10.0 * _clip01(1.0 - 0.5 * (np.mean(np.abs(luminance - np.fliplr(luminance))) / 255.0) - 0.5 * (np.mean(np.abs(luminance - np.flipud(luminance))) / 255.0))), 2),
        "Contrast": round(float(_score_target(contrast_std, 55.0, 25.0)), 2),
    }

    feature_weights = {
        "Content": 0.13,
        "ColorHarmony": 0.12,
        "Object": 0.10,
        "VividColor": 0.09,
        "Light": 0.09,
        "DoF": 0.09,
        "RuleOfThirds": 0.08,
        "BalacingElements": 0.07,
        "Repetition": 0.05,
        "MotionBlur": 0.07,
        "Symmetry": 0.05,
        "Contrast": 0.06,
    }

    composite_score = sum(feature_scores[k] * feature_weights[k] for k in feature_scores)
    composite_score = float(max(0.0, min(10.0, composite_score)))

    if composite_score >= 6.67:
        label = "good"
    elif composite_score >= 3.33:
        label = "average"
    else:
        label = "bad"

    contributions = []
    for feature_name in sorted(feature_scores.keys(), key=lambda name: feature_weights[name], reverse=True):
        score_value = float(feature_scores[feature_name])
        weight_value = float(feature_weights[feature_name])
        contributions.append({
            "feature": feature_name,
            "score_0_10": round(score_value, 2),
            "weight": round(weight_value, 3),
            "contribution": round(score_value * weight_value, 3),
        })

    return {
        "score_0_10": round(composite_score, 2),
        "class_label": label,
        "feature_scores": feature_scores,
        "feature_weights": feature_weights,
        "top_contributions": contributions[:5],
        "bottom_features": sorted(
            contributions,
            key=lambda item: item["score_0_10"],
        )[:3],
        "debug_metrics": {
            "brightness_0_255": round(brightness, 2),
            "contrast_std": round(contrast_std, 2),
            "vividness_0_1": round(vividness, 4),
            "edge_density_0_1": round(edge_density, 4),
            "laplacian_variance": round(lap_var, 2),
            "saliency_center_mass": round(center_mass, 4),
        },
    }


@torch.no_grad()
def predict_aesthetic(image_path, raw_attrs_dict=None, outputs_dir=None, device=None, use_tta=True):
    """Predict visual quality using the trained EfficientNet-B2 fusion model.

    If no attributes are supplied, neutral values are used for the 11 AADB features.
    Returns both the neural network score and interpretable visual feature breakdown.
    """
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

    artifacts = load_visual_model(outputs_dir, device=device)
    model = artifacts["model"]
    device = artifacts["device"]
    norm_stats = artifacts["norm_stats"]
    attr_cols = artifacts["attr_cols"]
    class_names = artifacts["class_names"]

    image = Image.open(image_path).convert("RGB")
    image_tensor = _build_image_tensor(image, use_tta=use_tta).to(device)

    attrs = normalize_attrs(raw_attrs_dict or {}, norm_stats, attr_cols)
    attrs_tensor = torch.tensor(attrs, dtype=torch.float32, device=device).unsqueeze(0)

    if use_tta:
        attrs_tensor = attrs_tensor.repeat(image_tensor.size(0), 1)
        logits, scores = model(image_tensor, attrs_tensor)
        probs = torch.softmax(logits, dim=1).mean(0)
        score_n = float(scores.mean().item())
    else:
        logits, score = model(image_tensor, attrs_tensor)
        probs = torch.softmax(logits, dim=1)[0]
        score_n = float(score.item())

    # Derive class FROM score to maintain consistency
    # Thresholds: bad [0, 3.33), average [3.33, 6.67), good [6.67, 10]
    score_0_10 = round(score_n * 10.0, 2)
    
    if score_0_10 < 3.33:
        class_id = 0  # bad
    elif score_0_10 < 6.67:
        class_id = 1  # average
    else:
        class_id = 2  # good
    
    # Use actual model probabilities instead of hardcoding
    class_probs_computed = {}
    for i, class_name in enumerate(class_names):
        class_probs_computed[class_name] = round(float(probs[i].item()), 4)
    
    model_confidence = float(probs[class_id].item())
    
    # Get interpretable visual feature breakdown (12 composition-based features)
    visual_features = detailed_feature_visual_score(image_path, outputs_dir=outputs_dir)

    # Ensure any expected attributes that are missing are present with 0.0
    expected_attrs = artifacts.get('attr_cols', DEFAULT_ATTR_COLS)
    for col in expected_attrs:
        if col not in visual_features.get('feature_scores', {}):
            visual_features.setdefault('feature_scores', {})[col] = 0.0
        if col not in visual_features.get('feature_weights', {}):
            visual_features.setdefault('feature_weights', {})[col] = 0.0

    # Recompute contribution summaries so they reflect any inserted zeros
    contributions = []
    for feature_name in sorted(visual_features['feature_scores'].keys(), key=lambda name: visual_features['feature_weights'].get(name, 0.0), reverse=True):
        score_value = float(visual_features['feature_scores'][feature_name])
        weight_value = float(visual_features['feature_weights'].get(feature_name, 0.0))
        contributions.append({
            "feature": feature_name,
            "score_0_10": round(score_value, 2),
            "weight": round(weight_value, 3),
            "contribution": round(score_value * weight_value, 3),
        })

    visual_features['top_contributions'] = contributions[:5]
    visual_features['bottom_features'] = sorted(contributions, key=lambda item: item['score_0_10'])[:3]

    # Use feature-based composite score as the primary score for alignment with feature breakdown
    # (not the neural network score, which can diverge from interpretable features)
    feature_based_score_0_10 = float(visual_features['score_0_10'])

    return {
        "class_label": class_names[class_id],
        "class_id": class_id,
        "score_0_10": feature_based_score_0_10,  # Feature-based composite, not neural network
        "confidence": round(model_confidence, 4),
        "class_probs": class_probs_computed,
        "model_source": "feature_composite_0_10_scoring",
        # Interpretable visual features breakdown (like text dimensions)
        "visual_features": {
            "feature_scores": visual_features["feature_scores"],
            "feature_weights": visual_features["feature_weights"],
            "top_contributions": visual_features["top_contributions"],
            "bottom_features": visual_features["bottom_features"],
        }
    }


def simple_image_quality_score(image_path, raw_attrs_dict=None, outputs_dir=None, device=None, use_tta=True):
    """Compatibility wrapper that now uses the trained visual model."""
    return predict_aesthetic(
        image_path=image_path,
        raw_attrs_dict=raw_attrs_dict,
        outputs_dir=outputs_dir,
        device=device,
        use_tta=use_tta,
    )


def extract_visual_regions_from_image(image_path):
    """Extract distinct visual regions (images, graphics, logos) from a screenshot.
    
    Uses edge detection to identify visual regions with good color/shape definition.
    Returns list of base64-encoded image crops with region metadata.
    """
    regions_list = []
    
    if cv2 is None:
        return regions_list
    
    try:
        import base64
        from io import BytesIO
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return regions_list
        
        height, width = img.shape[:2]
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply morphological operations to enhance visual regions
        # First, apply Canny edge detection with lower thresholds for more sensitivity
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges to connect nearby contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=3)
        
        # Close small holes to create more cohesive regions
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel_close)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return regions_list
        
        # More lenient size thresholds to catch visual regions
        min_area = (width * height) * 0.01  # At least 1% of image area
        max_area = (width * height) * 0.90  # At most 90% of image area
        min_width = 25
        min_height = 25
        
        extracted_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Filter by size
            if area < min_area or area > max_area:
                continue
            if w < min_width or h < min_height:
                continue
            
            # Skip very thin/elongated shapes (likely borders or lines)
            aspect_ratio = float(w) / float(h) if h > 0 else 0
            if aspect_ratio < 0.15 or aspect_ratio > 6.5:
                continue
            
            # Check for overlap with existing boxes
            is_overlapping = False
            for ex_x, ex_y, ex_w, ex_h in extracted_boxes:
                overlap_x = max(0, min(x + w, ex_x + ex_w) - max(x, ex_x))
                overlap_y = max(0, min(y + h, ex_y + ex_h) - max(y, ex_y))
                overlap_area = overlap_x * overlap_y
                if overlap_area > 0.3 * area:  # Skip if >30% overlapping
                    is_overlapping = True
                    break
            
            if is_overlapping:
                continue
            
            extracted_boxes.append((x, y, w, h))
        
        # Extract regions
        for x, y, w, h in extracted_boxes:
            # Add small margin
            margin = 2
            y1 = max(0, y - margin)
            y2 = min(height, y + h + margin)
            x1 = max(0, x - margin)
            x2 = min(width, x + w + margin)
            
            region_img = img[y1:y2, x1:x2]
            
            if region_img.size == 0:
                continue
            
            # Convert BGR to RGB for PIL
            region_rgb = cv2.cvtColor(region_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(region_rgb)
            
            # Encode to base64
            buffered = BytesIO()
            pil_img.save(buffered, format='PNG')
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Calculate region position (as percentage of image)
            pos_x = round(100.0 * x / width, 1)
            pos_y = round(100.0 * y / height, 1)
            
            regions_list.append({
                'data': img_str,
                'position': f'{pos_x}% from left, {pos_y}% from top',
                'size': f'{w}x{h}px',
                'area_percent': round(100.0 * (w * h) / (width * height), 1),
            })
        
        # Sort by position (top-to-bottom, left-to-right)
        regions_list.sort(key=lambda r: (r['position']))
        
        print(f"[DEBUG] Extracted {len(regions_list)} visual regions from {width}x{height} image")
        return regions_list[:10]  # Limit to 10 regions
        
    except Exception as e:
        print(f"Error extracting visual regions: {e}")
        import traceback
        traceback.print_exc()
        return regions_list


if __name__ == "__main__":
    print("visual_inference now loads the trained EfficientNet-B2 fusion model.")