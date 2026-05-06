"""XAI (Explainability) module for visual and text engagement prediction.

Provides:
- Grad-CAM for visual saliency maps (shows which image regions matter most)
- Feature attribution for fusion model decisions
- Attribution breakdowns for text dimensions
"""

import json
import os
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision import transforms
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from visual_inference import (
    AestheticFusionModel,
    load_visual_model,
    normalize_attrs,
    _resolve_device,
    _load_json,
)
from text_inference import extract_text_from_image


class GradCAM:
    """Grad-CAM: Gradient-weighted Class Activation Mapping for CNN interpretability."""

    def __init__(self, model, target_layer):
        """
        Args:
            model: PyTorch model (AestheticFusionModel)
            target_layer: layer to compute gradients for (e.g., model.img_backbone[-1])
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Hook to capture gradients (backward_hook receives tuple of gradients)
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        # Hook to capture activations
        def forward_hook(module, input, output):
            self.activations = output

        self.target_layer.register_backward_hook(backward_hook)
        self.target_layer.register_forward_hook(forward_hook)

    def generate(self, image_tensor, attrs_tensor, class_id):
        """
        Generate Grad-CAM heatmap for a given class.

        Args:
            image_tensor: (1, 3, 256, 256)
            attrs_tensor: (1, 11)
            class_id: target class (0=bad, 1=avg, 2=good)

        Returns:
            cam: (256, 256) heatmap
        """
        self.model.eval()
        with torch.enable_grad():
            cls_logits, _ = self.model(image_tensor, attrs_tensor)
            target_score = cls_logits[0, class_id]
            self.model.zero_grad()
            target_score.backward()

        # Grad-CAM formula: mean of gradients × activations
        gradients = self.gradients[0]  # (channels, height, width)
        activations = self.activations[0]  # (channels, height, width)

        weights = gradients.mean(dim=(1, 2))  # (channels,)
        cam = (weights.view(-1, 1, 1) * activations).sum(0)  # (height, width)
        cam = F.relu(cam)
        cam = cam / (cam.max() + 1e-8)

        return cam.detach().cpu().numpy()


def compute_grad_cam(
    image_path,
    raw_attrs_dict=None,
    outputs_dir=None,
    device=None,
    save_path=None,
    target_class_id=None,
    override_score_0_10=None,
):
    """
    Compute and visualize Grad-CAM for visual model prediction.

    Args:
        image_path: path to image
        raw_attrs_dict: raw AADB attributes
        outputs_dir: directory with model artifacts
        device: torch device
        save_path: where to save saliency overlay (if None, returns numpy only)

    Returns:
        dict with cam, predicted_class, score
    """
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

    device = _resolve_device(device)
    artifacts = load_visual_model(outputs_dir, device=device)
    model = artifacts["model"]
    attr_cols = artifacts["attr_cols"]
    norm_stats = artifacts["norm_stats"]
    class_names = artifacts["class_names"]

    # Load and preprocess image
    img = Image.open(image_path).convert("RGB")
    img_tensor = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])(img).unsqueeze(0).to(device)

    # Prepare attributes
    attrs = normalize_attrs(raw_attrs_dict or {}, norm_stats, attr_cols)
    attrs_tensor = torch.tensor(attrs, dtype=torch.float32, device=device).unsqueeze(0)

    # Forward pass to get prediction unless the notebook evaluation already
    # supplied the score/class that Grad-CAM should explain.
    with torch.no_grad():
        cls_logits, score = model(img_tensor, attrs_tensor)
        score_0_10 = float(score.item() * 10.0)

        if override_score_0_10 is not None:
            score_0_10 = float(override_score_0_10)

        if target_class_id is not None:
            pred_class = int(target_class_id)
        else:
            pred_class = _class_id_from_score(score_0_10)

        pred_score = score_0_10

    # Grad-CAM on target class
    grad_cam = GradCAM(model, model.img_backbone[-1])
    cam = grad_cam.generate(img_tensor, attrs_tensor, class_id=pred_class)

    # Resize CAM to image size
    cam_resized = np.kron(cam, np.ones((256 // cam.shape[0], 256 // cam.shape[1])))

    # Overlay on original image
    if save_path is None:
        save_path = os.path.join(
            outputs_dir, f"gradcam_{os.path.basename(image_path)}"
        )

    img_np = np.array(img.resize((256, 256)))
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Original image
    axes[0].imshow(img_np)
    axes[0].set_title("Original Image")
    axes[0].axis("off")

    # Grad-CAM heatmap
    axes[1].imshow(cam_resized, cmap="hot")
    axes[1].set_title(f"Grad-CAM ({class_names[pred_class]})")
    axes[1].axis("off")

    # Overlay
    axes[2].imshow(img_np)
    im = axes[2].imshow(cam_resized, cmap="jet", alpha=0.4)
    axes[2].set_title(f"Overlay (score={pred_score:.1f}/10)")
    axes[2].axis("off")
    plt.colorbar(im, ax=axes[2], fraction=0.046)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {
        "gradcam_heatmap": cam,  # raw heatmap
        "gradcam_save_path": save_path,
        "predicted_class": class_names[pred_class],
        "class_id": pred_class,
        "score_0_10": pred_score,
        "top_regions_description": _describe_top_regions(cam),
    }


def _describe_top_regions(cam, top_k=5):
    """Describe spatial regions with highest activation in Grad-CAM."""
    # Find top-k activations
    flat_cam = cam.flatten()
    top_indices = np.argsort(flat_cam)[-top_k:][::-1]
    top_values = flat_cam[top_indices]

    descriptions = []
    for i, (idx, val) in enumerate(zip(top_indices, top_values)):
        row, col = divmod(idx, cam.shape[1])
        region = f"row={row}/{cam.shape[0]}, col={col}/{cam.shape[1]}"
        descriptions.append(f"Region {i+1}: {region} (intensity={val:.3f})")

    return descriptions


def _class_id_from_score(score_0_10):
    """Map the notebook score to the same class bands used by visual inference."""
    if score_0_10 < 3.33:
        return 0
    if score_0_10 < 6.67:
        return 1
    return 2


def compute_feature_attribution(
    image_path,
    raw_attrs_dict=None,
    outputs_dir=None,
    device=None,
):
    """
    Extract per-attribute importance for visual prediction.

    Uses the model's attribute encoder and fusion MLP to quantify
    how much each AADB attribute contributes to the final score.

    Args:
        image_path: path to image
        raw_attrs_dict: raw attributes
        outputs_dir: model artifacts directory
        device: torch device

    Returns:
        dict with attribute importance scores
    """
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

    device = _resolve_device(device)
    artifacts = load_visual_model(outputs_dir, device=device)
    model = artifacts["model"]
    attr_cols = artifacts["attr_cols"]
    norm_stats = artifacts["norm_stats"]

    # Image preprocessing
    img = Image.open(image_path).convert("RGB")
    img_tensor = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])(img).unsqueeze(0).to(device)

    # Normalize attributes
    attrs = normalize_attrs(raw_attrs_dict or {}, norm_stats, attr_cols)
    attrs_tensor = torch.tensor(attrs, dtype=torch.float32, device=device).unsqueeze(0)

    model.eval()
    with torch.no_grad():
        # Get image features
        img_feat = model.img_backbone(img_tensor)
        img_feat = img_feat.view(img_feat.size(0), -1)
        img_feat = model.img_neck(img_feat)

        # Attribute features
        attr_feat = model.attr_encoder(attrs_tensor)

        # Fusion with gradient tracking for attribution
        attrs_tensor.requires_grad_(True)
        if attrs_tensor.grad is not None:
            attrs_tensor.grad.zero_()

        fused = torch.cat([img_feat.detach(), attr_feat], dim=1)
        fused = model.fusion(fused)
        score = model.score_head(fused).squeeze(1)

    # Attribute contribution: L2 norm of encoder weights × normalized attributes
    attr_importance = {}
    with torch.no_grad():
        for i, col in enumerate(attr_cols):
            # Weight by encoder layer norms
            w1 = model.attr_encoder[0].weight[i, :].abs().sum().item()
            attr_importance[col] = float(w1 * abs(float(attrs[i])))

    # Normalize to 0-1
    max_imp = max(attr_importance.values()) if attr_importance else 1.0
    attr_importance = {k: v / (max_imp + 1e-8) for k, v in attr_importance.items()}

    return {
        "attribute_importance": attr_importance,
        "top_3_attributes": sorted(
            attr_importance.items(), key=lambda x: x[1], reverse=True
        )[:3],
    }


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
        "file_size_kb": os.path.getsize(image_path) / 1024,
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


def generate_xai_report(
    image_path,
    raw_attrs_dict=None,
    outputs_dir=None,
    device=None,
    actual_visual_score=None,
    visual_eval_result=None,
):
    """Generate full XAI report: Grad-CAM + feature attribution + image composition + extracted text.
    
    Args:
        image_path: path to image
        raw_attrs_dict: raw attributes dict
        outputs_dir: model artifacts directory
        device: torch device
        actual_visual_score: the ACTUAL visual score from feature-based evaluation (use this instead of model score)
    """
    if outputs_dir is None:
        outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

    if visual_eval_result is None and isinstance(actual_visual_score, dict):
        visual_eval_result = actual_visual_score
        actual_visual_score = visual_eval_result.get("score_0_10")

    actual_visual_class = None
    actual_visual_label = None
    if isinstance(visual_eval_result, dict):
        actual_visual_score = visual_eval_result.get("score_0_10", actual_visual_score)
        actual_visual_class = visual_eval_result.get("class_id")
        actual_visual_label = visual_eval_result.get("class_label")

    # Grad-CAM (for visualization only; we'll override the score with actual_visual_score)
    grad_cam_res = compute_grad_cam(
        image_path,
        raw_attrs_dict,
        outputs_dir,
        device,
        target_class_id=actual_visual_class,
        override_score_0_10=actual_visual_score,
    )

    # Feature attribution
    feat_attr_res = compute_feature_attribution(
        image_path, raw_attrs_dict, outputs_dir, device
    )
    
    # Image composition analysis
    composition = analyze_image_composition(image_path)
    
    # Extract text from image
    extracted_text = extract_text_from_image(image_path)

    # Load attribute importance from training
    attr_importance_json = os.path.join(outputs_dir, "attribute_importance.json")
    training_attr_importance = {}
    if os.path.exists(attr_importance_json):
        with open(attr_importance_json, 'r') as f:
            training_attr_importance = json.load(f)

    # Use the notebook-trained visual score if provided; otherwise fall back to the internal model score.
    if actual_visual_score is not None:
        display_score = float(actual_visual_score)
        display_class = actual_visual_label or ["bad", "average", "good"][_class_id_from_score(display_score)]
    else:
        display_score = grad_cam_res["score_0_10"]
        display_class = grad_cam_res["predicted_class"]
    
    report = {
        "image": image_path,
        "image_composition": composition,
        "extracted_text": extracted_text,
        "visual_prediction": {
            "class": display_class,
            "score_0_10": display_score,
            "class_id": actual_visual_class if actual_visual_class is not None else grad_cam_res.get("class_id"),
            "source": "notebook_visual_evaluation" if actual_visual_score is not None else "model_inference",
        },
        "grad_cam": {
            "heatmap_save": grad_cam_res["gradcam_save_path"],
            "top_regions": grad_cam_res["top_regions_description"],
        },
        "attribute_importance_inference": {
            "top_3": feat_attr_res["top_3_attributes"],
            "full": feat_attr_res["attribute_importance"],
        },
        "attribute_importance_training": training_attr_importance,
        "interpretation": (
            f"The notebook-trained visual score is {display_score:.1f}/10, which falls in the '{display_class}' band. "
            f"Image: {composition['dimensions']['width']}x{composition['dimensions']['height']} "
            f"({composition['aspect_ratio']}:1), {composition['brightness_label']} with {composition['contrast_label']} contrast. "
            f"Image regions with highest activation shown in Grad-CAM heatmap. "
            f"Top influencing attributes: "
            + ", ".join([f"{attr}({imp:.2f})" for attr, imp in feat_attr_res["top_3_attributes"]])
        ),
        "score_source": "notebook_visual_evaluation" if actual_visual_score is not None else "model_inference",
    }

    # Save report
    report_path = os.path.join(outputs_dir, "xai_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return {**report, "report_save_path": report_path}


if __name__ == "__main__":
    print("XAI inference module for visual engagement prediction.")
