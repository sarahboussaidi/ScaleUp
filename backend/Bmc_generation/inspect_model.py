"""Inspect the text classifier model to see its actual class labels."""

import os
from transformers import AutoConfig

TEXT_CLASSIFIER_PATH = os.path.join(
    os.path.dirname(__file__),
    'models/bmc_generation/text_classifier'
)

try:
    print(f"Loading config from: {TEXT_CLASSIFIER_PATH}")
    config = AutoConfig.from_pretrained(TEXT_CLASSIFIER_PATH)
    
    print("\n" + "="*60)
    print("MODEL CONFIGURATION")
    print("="*60)
    print(f"Number of labels: {config.num_labels}")
    print(f"\nid2label mapping:")
    for idx, label in sorted(config.id2label.items()):
        print(f"  {idx}: '{label}'")
    
    print(f"\nlabel2id mapping:")
    for label, idx in sorted(config.label2id.items()):
        print(f"  '{label}': {idx}")
    
    print("\n" + "="*60)
    print("EXPECTED BMC_BLOCKS:")
    print("="*60)
    BMC_BLOCKS = [
        "channels",
        "customer_segments",
        "value_proposition",
        "customer_relationships",
        "revenue_streams",
        "key_resources",
        "key_activities",
        "key_partnerships",
        "cost_structure",
        "other"
    ]
    for i, block in enumerate(BMC_BLOCKS):
        print(f"  {i}: '{block}'")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
