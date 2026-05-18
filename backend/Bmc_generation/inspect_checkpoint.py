import torch

checkpoint = torch.load('models/bmc_generation/best_doc_type_classifier.pth', map_location='cpu', weights_only=False)

print('Checkpoint keys:', list(checkpoint.keys()))
print()
if 'class_names' in checkpoint:
    print(f'Number of class names: {len(checkpoint["class_names"])}')
    print(f'All class names: {checkpoint["class_names"]}')
    print()

if 'class_to_idx' in checkpoint:
    print()
    print(f'class_to_idx mapping (first 20): {dict(list(checkpoint["class_to_idx"].items())[:20])}')
    print(f'Total classes in class_to_idx: {len(checkpoint["class_to_idx"])}')

# Check actual state dict size
state_dict = checkpoint['model_state_dict']
if 'classifier.1.weight' in state_dict:
    print()
    print(f"Actual classifier.1.weight shape: {state_dict['classifier.1.weight'].shape}")
    print(f"This means the model has {state_dict['classifier.1.weight'].shape[0]} output classes")

