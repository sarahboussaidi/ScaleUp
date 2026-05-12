"""
bmc_eval_scripts/text_classifier.py
Step 3 — Text Type Classifier (LSTM)
Loads bmc_text_cnn_best.pt + model_config.json and classifies each section
as HANDWRITTEN or TYPED.
"""

import json
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

MODEL_PATH = Path("bmc_eval_models/bmc_text_cnn_best.pt")
CONFIG_PATH = Path("bmc_eval_models/model_config.json")


# ── Model architecture (must match training code) ─────────────────────────────

class PatchEmbedding(nn.Module):
    def __init__(self, patch_dim: int, embed_dim: int, dropout: float = 0.2):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(patch_dim, embed_dim, bias=False),
            nn.LayerNorm(embed_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.proj(x)


class AttentionPooling(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.W = nn.Linear(hidden_size, hidden_size, bias=True)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, lstm_out: torch.Tensor):
        scores  = self.v(torch.tanh(self.W(lstm_out)))
        weights = F.softmax(scores.squeeze(-1), dim=1)
        context = (weights.unsqueeze(-1) * lstm_out).sum(dim=1)
        return context, weights


class BMCTextLSTM(nn.Module):
    def __init__(self, patch_dim, embed_dim, hidden_size, num_layers, num_classes, dropout=0.3):
        super().__init__()
        self.patch_embed = PatchEmbedding(patch_dim, embed_dim, dropout=0.2)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=False,
        )
        self.attention = AttentionPooling(hidden_size)
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(hidden_size, 128),
            nn.LayerNorm(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, patches: torch.Tensor):
        embedded = self.patch_embed(patches)
        lstm_out, _ = self.lstm(embedded)
        context, weights = self.attention(lstm_out)
        logits = self.classifier(context)
        return logits, weights


# ── Classifier ────────────────────────────────────────────────────────────────

class TextClassifier:
    def __init__(self):
        self.model = None
        self.config = None
        self.labels = None
        self.img_size = 224
        self.n_patches = 16
        self.patch_dim = 9408

    def load(self):
        if self.model is not None:
            return

        with open(CONFIG_PATH) as f:
            self.config = json.load(f)

        self.img_size  = self.config["img_size"]
        self.n_patches = self.config["n_patches"]
        self.patch_dim = self.config["patch_dim"]
        embed_dim      = self.config["embed_dim"]
        hidden_size    = self.config["hidden_size"]
        num_classes    = self.config["num_classes"]
        self.labels    = self.config["class_names"]

        checkpoint = torch.load(MODEL_PATH, map_location="cpu")

        self.model = BMCTextLSTM(
            patch_dim=self.patch_dim,
            embed_dim=embed_dim,
            hidden_size=hidden_size,
            num_layers=2,
            num_classes=num_classes,
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def _preprocess(self, image: Image.Image) -> torch.Tensor:
        import torchvision.transforms as T

        transform = T.Compose([
            T.Resize((self.img_size, self.img_size)),
            T.Grayscale(num_output_channels=3),
            T.ToTensor(),
            T.Normalize([0.5]*3, [0.5]*3),
        ])
        img_tensor = transform(image)

        C, H, W = img_tensor.shape
        patch_h = H // self.n_patches
        patches = []
        for i in range(self.n_patches):
            patch = img_tensor[:, i*patch_h:(i+1)*patch_h, :]
            patches.append(patch.flatten())

        x = torch.stack(patches).unsqueeze(0)
        return x

    def classify(self, image: Image.Image) -> str:
        self.load()
        tensor = self._preprocess(image)
        with torch.no_grad():
            logits, _ = self.model(tensor)
            pred = int(torch.argmax(logits, dim=1).item())
        return self.labels[pred]


# ── Module-level singleton ────────────────────────────────────────────────────

_classifier = TextClassifier()


def classify(image: Image.Image) -> str:
    return _classifier.classify(image)


def classify_sections(sections: list) -> list:
    for section in sections:
        section["text_type"] = classify(section["crop"])
    return sections