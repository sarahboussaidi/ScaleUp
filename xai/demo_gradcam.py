"""Lightweight CLI demo to produce Grad-CAM overlays for signature models.

Usage:
    python xai/demo_gradcam.py --image path/to/image.jpg

If no image is provided the script will pick the first jpg/png it finds under the project.
"""
from pathlib import Path
import argparse
import sys

from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from chatbot_api import _load_signature_model, _load_pth_model, GENERATED_DIR
from xai.gradcam import GradCAM, overlay_cam_on_image


def find_any_image(root: Path) -> Path:
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        files = list(root.rglob(ext))
        if files:
            return files[0]
    raise FileNotFoundError("No images found in repository to run demo on. Provide --image instead.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    model, transform, model_path = _load_signature_model()

    # If a scripted model was returned, prefer a .pth variant if available (hooks require real nn.Module)
    if "script" in model_path.name.lower():
        pth_candidates = [
            PROJECT_ROOT / "best_signature_resnet18.pth",
            PROJECT_ROOT / "best_signature_cnn.pth",
            PROJECT_ROOT / "best_signature_vit.pth",
        ]
        fallback = None
        for p in pth_candidates:
            if p.exists():
                fallback = p
                break
        if fallback:
            model, transform = _load_pth_model(fallback)
            model_path = fallback
        else:
            print("Scripted model detected and no .pth fallback found. Grad-CAM requires a non-scripted model.")
            print("Consider converting your scripted model back to state_dict (.pth) or pass a .pth model file.")
            return

    # choose image
    if args.image:
        img_path = Path(args.image)
        if not img_path.exists():
            raise FileNotFoundError(args.image)
    else:
        img_path = find_any_image(PROJECT_ROOT)

    img = Image.open(img_path).convert("RGB")
    input_tensor = transform(img).unsqueeze(0)  # 1xCxHxW

    device = torch.device("cpu")
    model = model.to(device)

    # select target conv layer by heuristic inside GradCAM
    cammer = GradCAM(model)
    cam = cammer.generate_cam(input_tensor)

    overlay = overlay_cam_on_image(img, cam, alpha=0.5)

    stamp = Path(img_path).stem
    out_name = args.output or f"gradcam_{stamp}_{model_path.name}.png"
    out_path = GENERATED_DIR / out_name
    overlay.save(out_path)
    print(f"Saved Grad-CAM overlay to: {out_path}")


if __name__ == "__main__":
    main()
