import typing
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: typing.Optional[nn.Module] = None):
        self.model = model
        self.model.eval()
        self.activations = None
        self.gradients = None

        if target_layer is None:
            target_layer = self._find_target_layer(self.model)
        self.target_layer = target_layer

        # register hooks
        def forward_hook(module, inp, out):
            self.activations = out.detach()

        def backward_hook(module, grad_in, grad_out):
            # grad_out is a tuple
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def _find_target_layer(self, model: nn.Module) -> nn.Module:
        # find the last Conv2d module in the network
        for name, module in reversed(list(model.named_modules())):
            if isinstance(module, nn.Conv2d):
                return module
        raise ValueError("No Conv2d layer found in model to target for Grad-CAM")

    def generate_cam(self, input_tensor: torch.Tensor, class_idx: typing.Optional[int] = None) -> np.ndarray:
        """Returns a HxW numpy array with values in [0,1].

        input_tensor: torch.Tensor shape (1,C,H,W)
        """
        device = next(self.model.parameters()).device
        input_tensor = input_tensor.to(device)
        input_tensor = input_tensor.clone().detach().requires_grad_(True)

        # forward
        out = self.model(input_tensor)
        if class_idx is None:
            class_idx = int(out.argmax(dim=1).item())

        # backward on chosen class score
        self.model.zero_grad()
        score = out[0, class_idx]
        score.backward(retain_graph=False)

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Hooks did not capture activations/gradients. Check model and target layer.")

        # gradients: (N, C, H, W)
        grads = self.gradients[0]
        acts = self.activations[0]

        weights = grads.mean(dim=(1, 2))  # global-average-pool
        cam = torch.zeros(acts.shape[1:], dtype=acts.dtype, device=acts.device)
        for i, w in enumerate(weights):
            cam += w * acts[i]

        cam = F.relu(cam)
        cam = cam.unsqueeze(0).unsqueeze(0)  # 1x1xHxW for interpolate
        cam = F.interpolate(cam, size=input_tensor.shape[2:], mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        # normalize
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        return cam


def overlay_cam_on_image(pil_img, cam: np.ndarray, alpha: float = 0.5, colormap="jet"):
    """Overlay a CAM (HxW, 0..1) on a PIL image and return a PIL image."""
    from PIL import Image
    import matplotlib.cm as cm

    img = pil_img.convert("RGB")
    img_np = np.array(img).astype(np.float32) / 255.0

    cmap = cm.get_cmap(colormap)
    heatmap = cmap(cam)[:, :, :3]

    # resize heatmap to image size
    from PIL import Image as _Image

    heatmap_img = _Image.fromarray((heatmap * 255).astype(np.uint8))
    heatmap_resized = heatmap_img.resize(img.size, resample=_Image.BILINEAR)
    heatmap = np.array(heatmap_resized).astype(np.float32) / 255.0

    overlay = (1 - alpha) * img_np + alpha * heatmap
    overlay = np.clip(overlay * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(overlay)


def cam_stats(cam: np.ndarray, threshold_quantile: float = 0.85) -> dict:
    """Compute interpretable Grad-CAM statistics from a normalized heatmap."""
    if cam.ndim != 2:
        raise ValueError("cam must be a 2D array")

    h, w = cam.shape
    threshold = float(np.quantile(cam, threshold_quantile))
    mask = cam >= threshold

    if not mask.any():
        max_idx = np.unravel_index(int(np.argmax(cam)), cam.shape)
        mask[max_idx] = True

    # Keep the largest connected salient component for a tighter focus box.
    labels = np.full(mask.shape, -1, dtype=np.int32)
    label_id = 0
    best_label = -1
    best_size = 0
    h_idx, w_idx = mask.shape

    for r in range(h_idx):
        for c in range(w_idx):
            if not mask[r, c] or labels[r, c] != -1:
                continue
            stack = [(r, c)]
            labels[r, c] = label_id
            size = 0

            while stack:
                rr, cc = stack.pop()
                size += 1
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h_idx and 0 <= nc < w_idx and mask[nr, nc] and labels[nr, nc] == -1:
                        labels[nr, nc] = label_id
                        stack.append((nr, nc))

            if size > best_size:
                best_size = size
                best_label = label_id
            label_id += 1

    if best_label != -1:
        focus_mask = labels == best_label
    else:
        focus_mask = mask

    ys, xs = np.where(focus_mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())

    area_ratio = float(mask.mean())
    centroid_y = float(ys.mean() / max(h - 1, 1))
    centroid_x = float(xs.mean() / max(w - 1, 1))
    mean_intensity = float(cam[mask].mean())
    max_intensity = float(cam.max())

    return {
        "threshold": round(threshold, 4),
        "salient_area_ratio": round(area_ratio, 4),
        "centroid_norm_xy": [round(centroid_x, 4), round(centroid_y, 4)],
        "focus_box_norm_xyxy": [
            round(x0 / max(w - 1, 1), 4),
            round(y0 / max(h - 1, 1), 4),
            round(x1 / max(w - 1, 1), 4),
            round(y1 / max(h - 1, 1), 4),
        ],
        "mean_salient_intensity": round(mean_intensity, 4),
        "max_intensity": round(max_intensity, 4),
    }


def draw_focus_box(pil_img, box_norm_xyxy: typing.List[float], color=(255, 255, 255), width: int = 3):
    """Draw normalized focus box [x0,y0,x1,y1] onto a PIL image."""
    from PIL import ImageDraw

    img = pil_img.convert("RGB").copy()
    w, h = img.size
    x0 = int(box_norm_xyxy[0] * (w - 1))
    y0 = int(box_norm_xyxy[1] * (h - 1))
    x1 = int(box_norm_xyxy[2] * (w - 1))
    y1 = int(box_norm_xyxy[3] * (h - 1))

    draw = ImageDraw.Draw(img)
    for i in range(width):
        draw.rectangle([x0 - i, y0 - i, x1 + i, y1 + i], outline=color)
    return img
