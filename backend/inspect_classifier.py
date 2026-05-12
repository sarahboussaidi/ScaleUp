"""
inspect_classifier.py
Run from project root: python inspect_classifier.py
Tells us how the model was saved so we can load it correctly.
"""

import torch
import json
from pathlib import Path

MODEL_PATH = Path("bmc_eval_models/bmc_text_cnn_best.pt")
CONFIG_PATH = Path("bmc_eval_models/model_config.json")

print("=== model_config.json ===")
with open(CONFIG_PATH) as f:
    config = json.load(f)
print(json.dumps(config, indent=2))

print("\n=== bmc_text_cnn_best.pt contents ===")
obj = torch.load(MODEL_PATH, map_location="cpu")
print(f"Type: {type(obj)}")

if isinstance(obj, dict):
    print(f"Keys: {list(obj.keys())}")
elif hasattr(obj, "state_dict"):
    print("Full model object (has state_dict)")
else:
    print(f"Unknown type: {type(obj)}")