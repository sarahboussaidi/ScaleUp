"""
Document Type Classifier Routes
Integrates EfficientNetB0 model for classifying uploaded images into:
- BMC image
- Handwritten note
- Typed document
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from flask import Blueprint, request, jsonify
import io
from PIL import Image
import os
import numpy as np
import traceback

# Create Blueprint
doc_classifier_bp = Blueprint('document_classifier', __name__)

# Model configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_CONFIG = {
    'checkpoint_path': os.path.join(
        BASE_DIR,
        'models',
        'bmc_generation',
        'efficientnet.pth'
    ),
    'image_size': 224,
    'class_names': ['bmc', 'handwritten', 'typed'],
    'num_classes': 3,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
}

# Global model storage
loaded_model = None
device = MODEL_CONFIG['device']


def load_document_classifier_model():
    """
    Load the EfficientNetB0 model from checkpoint.
    Trained with 3 classes: bmc, non_bmc_handwritten, non_bmc_typed
    Returns the model in evaluation mode.
    """
    global loaded_model
    
    if loaded_model is not None:
        print(f"✓ Model already loaded")
        return loaded_model
    
    try:
        checkpoint_path = MODEL_CONFIG['checkpoint_path']
        print(f"Loading document classifier from {checkpoint_path}")
        
        # Load checkpoint
        checkpoint = torch.load(
            checkpoint_path,
            map_location=device,
            weights_only=False
        )
        
        print(f"Checkpoint keys: {list(checkpoint.keys())}")
        
        # Get class info from checkpoint
        checkpoint_classes = checkpoint.get('class_names', ['bmc', 'non_bmc_handwritten', 'non_bmc_typed'])
        print(f"Classes: {checkpoint_classes}")
        num_classes = len(checkpoint_classes)
        
        # Create EfficientNetB0 with 3 output classes using timm
        print(f"Creating EfficientNetB0 with {num_classes} output classes...")
        try:
            import timm
            model = timm.create_model(
                'efficientnet_b0',
                pretrained=False,
                num_classes=num_classes,
                drop_rate=0.5
            )
            print("✓ Created EfficientNetB0 with timm")
        except ImportError:
            print("⚠️  timm not available, using torchvision EfficientNetB0")
            model = models.efficientnet_b0(weights=None)
            # Modify classifier to output 3 classes
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, num_classes)
        
        # Load state dict with strict=False to handle any architecture mismatches
        print("Loading model weights from checkpoint...")
        try:
            model.load_state_dict(checkpoint['model_state_dict'], strict=True)
            print("✓ Loaded weights (strict mode)")
        except RuntimeError as e:
            print(f"Strict loading failed: {e}")
            print("Attempting with strict=False...")
            model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            print("✓ Loaded weights (strict=False)")
        
        # Debug: Check if classifier weights were actually loaded
        print("\n[DEBUG] Checking loaded weights...")
        with torch.no_grad():
            # Find classifier layer
            classifier = None
            if hasattr(model, 'classifier'):
                classifier = model.classifier
                print(f"[DEBUG] Classifier type: {type(classifier)}")
                print(f"[DEBUG] Classifier: {classifier}")
                
                if hasattr(classifier, 'weight'):
                    w = classifier.weight
                    print(f"[DEBUG] Classifier weight shape: {w.shape}")
                    print(f"[DEBUG] Classifier weight stats - min: {w.min():.6f}, max: {w.max():.6f}, mean: {w.mean():.6f}, std: {w.std():.6f}")
                    print(f"[DEBUG] Class bias: {classifier.bias}")
        
        # Move to device and eval mode
        model = model.to(device)
        model.eval()
        
        # Store class info in model
        model.checkpoint_classes = checkpoint_classes
        
        loaded_model = model
        print(f"✓ Document classifier loaded successfully")
        print(f"  Classes: {checkpoint_classes}")
        print(f"  Device: {device}")
        return model
        
    except Exception as e:
        print(f"✗ Error loading document classifier: {str(e)}")
        traceback.print_exc()
        return None

def compute_bmc_layout_score(image):
    """
    Simple visual verification for BMC layout.
    BMC images usually are landscape and contain many horizontal/vertical grid lines.
    """
    try:
        img = np.array(image.convert("RGB"))
        gray = np.mean(img, axis=2).astype(np.uint8)

        h, w = gray.shape
        aspect_ratio = w / float(h)

        # Detect dark grid lines
        edges = gray < 80

        vertical_projection = edges.mean(axis=0)
        horizontal_projection = edges.mean(axis=1)

        vertical_lines = np.sum(vertical_projection > 0.25)
        horizontal_lines = np.sum(horizontal_projection > 0.25)

        vertical_ratio = vertical_lines / max(1, w)
        horizontal_ratio = horizontal_lines / max(1, h)

        score = 0

        if aspect_ratio > 1.25:
            score += 1

        if vertical_ratio > 0.01:
            score += 1

        if horizontal_ratio > 0.01:
            score += 1

        print(
            f"[BMC-LAYOUT-CHECK] aspect={aspect_ratio:.2f}, "
            f"vertical_ratio={vertical_ratio:.4f}, "
            f"horizontal_ratio={horizontal_ratio:.4f}, score={score}"
        )

        return score

    except Exception as e:
        print(f"[BMC-LAYOUT-CHECK] Failed: {e}")
        return 0
def preprocess_image(image_file):
    """
    Preprocess uploaded image for model inference.
    
    Args:
        image_file: Flask FileStorage object
        
    Returns:
        Preprocessed image tensor on device
    """
    try:
        # Open image
        raw_bytes = image_file.read()
        print(f"[DEBUG] Opening image: {image_file.filename}, size: {len(raw_bytes)} bytes")
        image_file.seek(0)  # Reset file pointer
        image = Image.open(io.BytesIO(raw_bytes)).convert('RGB')
        global last_image_metadata

        w, h = image.size
        aspect_ratio = w / float(h) if h != 0 else 0
        bmc_layout_score = compute_bmc_layout_score(image)

        last_image_metadata = {
            "width": w,
            "height": h,
            "aspect_ratio": aspect_ratio,
            "bmc_layout_score": bmc_layout_score
        }
        print(f"[DEBUG] Image opened: mode={image.mode}, size={image.size}")

        # Save original image for debugging inspection
        try:
            debug_dir = os.path.join(os.path.dirname(__file__), 'debug_images')
            os.makedirs(debug_dir, exist_ok=True)
            safe_name = os.path.basename(image_file.filename)
            orig_path = os.path.join(debug_dir, f"orig_{safe_name}")
            image.save(orig_path)
            print(f"[DEBUG] Saved original image to: {orig_path}")
        except Exception as e:
            print(f"[DEBUG] Could not save original image: {e}")

        # Print aspect ratio to help debugging misclassification between typed/handwritten
        w, h = image.size
        aspect = w / float(h) if h != 0 else 0
        print(f"[DEBUG] Image aspect ratio: {aspect:.4f} (w={w}, h={h})")

        # Define preprocessing pipeline (aspect-preserving: resize shorter side then center-crop)
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(MODEL_CONFIG['image_size']),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet mean
                std=[0.229, 0.224, 0.225]    # ImageNet std
            )
        ])
        
        # Apply preprocessing
        image_tensor = preprocess(image)
        print(f"[DEBUG] After preprocessing: shape={image_tensor.shape}, min={image_tensor.min():.4f}, max={image_tensor.max():.4f}, mean={image_tensor.mean():.4f}")
        
        # Add batch dimension
        image_tensor = image_tensor.unsqueeze(0)
        print(f"[DEBUG] After unsqueeze: shape={image_tensor.shape}")
        
        # Move to device
        image_tensor = image_tensor.to(device)
        print(f"[DEBUG] After device transfer: device={image_tensor.device}, dtype={image_tensor.dtype}")
        
        return image_tensor
        
    except Exception as e:
        print(f"✗ Error preprocessing image: {str(e)}")
        traceback.print_exc()
        raise ValueError(f"Failed to preprocess image: {str(e)}")


def predict_document_type(image_tensor):
    """
    Run inference on preprocessed image.
    
    Args:
        image_tensor: Preprocessed image tensor
        
    Returns:
        Dictionary with document_type and confidence
    """
    try:
        model = loaded_model
        
        if model is None:
            raise RuntimeError("Model not loaded")
        
        with torch.no_grad():
            # Get model output
            logits = model(image_tensor)
            print(f"Logits shape: {logits.shape}")
            print(f"Logits: {logits}")
            
            # Apply softmax to get probabilities
            probabilities = torch.softmax(logits, dim=1)
            print(f"Probabilities: {probabilities}")
            
            # Get class with highest probability
            confidence, predicted_class = torch.max(probabilities, 1)
            
            # Get predicted class index and confidence
            class_idx = predicted_class.item()
            confidence_value = confidence.item()

            # Use checkpoint class names stored on the model when available
            checkpoint_classes = getattr(model, 'checkpoint_classes', None)
            if not checkpoint_classes:
                # fallback to default ordering
                checkpoint_classes = ['bmc', 'non_bmc_handwritten', 'non_bmc_typed']

            checkpoint_class_name = checkpoint_classes[class_idx]

            # Map checkpoint class names to our standard names
            class_mapping = {
                'bmc': 'bmc',
                'non_bmc_handwritten': 'handwritten',
                'non_bmc_typed': 'typed',
                'handwritten': 'handwritten',
                'typed': 'typed',
            }

            standard_class_name = class_mapping.get(checkpoint_class_name, checkpoint_class_name)

            # Build a probabilities dict using checkpoint class ordering and mapping to standard names
            all_probs = {}
            for idx, name in enumerate(checkpoint_classes):
                std_name = class_mapping.get(name, name)
                # accumulate probabilities if multiple checkpoint names map to same standard name
                p = float(probabilities[0, idx].item())
                if std_name in all_probs:
                    all_probs[std_name] += p
                else:
                    all_probs[std_name] = p

            # Ensure standard keys exist in returned probabilities
            for k in ['bmc', 'handwritten', 'typed']:
                all_probs.setdefault(k, 0.0)
            global last_image_metadata

            bmc_prob = all_probs.get("bmc", 0.0)
            typed_prob = all_probs.get("typed", 0.0)
            handwritten_prob = all_probs.get("handwritten", 0.0)

            layout_score = last_image_metadata.get("bmc_layout_score", 0)
            aspect_ratio = last_image_metadata.get("aspect_ratio", 0)

            # Safety correction:
            # If EfficientNet says BMC but the image does not visually look like a BMC,
            # redirect it to typed/handwritten based on the next strongest class.
            if standard_class_name == "bmc":
                if layout_score < 2:
                    print("[POST-FIX] Predicted BMC but layout check failed.")

                    if typed_prob >= handwritten_prob:
                        standard_class_name = "typed"
                        confidence_value = typed_prob
                    else:
                        standard_class_name = "handwritten"
                        confidence_value = handwritten_prob

                elif bmc_prob < 0.75:
                    print("[POST-FIX] BMC probability too low, correcting to typed.")
                    standard_class_name = "typed"
                    confidence_value = typed_prob
                        

            print(f"✓ Prediction: class_idx={class_idx}, class={checkpoint_class_name}, mapped={standard_class_name}, confidence={confidence_value:.4f}")

        return {
            'document_type': standard_class_name,
            'confidence': round(confidence_value, 4),
            'class_index': class_idx,
            'checkpoint_class': checkpoint_class_name,
            'all_probabilities': {k: round(v, 4) for k, v in all_probs.items()}
        }
        
    except Exception as e:
        print(f"✗ Error during prediction: {str(e)}")
        traceback.print_exc()
        raise RuntimeError(f"Prediction failed: {str(e)}")


# ==================== Flask Routes ====================

@doc_classifier_bp.route('/predict-document-type', methods=['POST'])
def predict_document_type_endpoint():
    """
    POST /predict-document-type
    
    Endpoint to classify uploaded image document type.
    
    Expected request:
    - File upload with key 'file'
    - Content-Type: multipart/form-data
    
    Returns:
    {
        "document_type": "handwritten",  # or "bmc" or "typed"
        "confidence": 0.9456,
        "class_index": 1,
        "all_probabilities": {
            "bmc": 0.0234,
            "handwritten": 0.9456,
            "typed": 0.031
        }
    }
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload an image file with key "file"'
            }), 400
        
        image_file = request.files['file']
        
        # Check if file is empty
        if image_file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Check file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        file_ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else None
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Allowed types: {", ".join(allowed_extensions)}'
            }), 400
        
        # Preprocess image
        image_tensor = preprocess_image(image_file)

        # Make prediction
        result = predict_document_type(image_tensor)

        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid image',
            'message': str(e)
        }), 400
        
    except Exception as e:
        print(f"✗ Error in predict_document_type_endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e)
        }), 500


@doc_classifier_bp.route('/model-info', methods=['GET'])
def get_model_info():
    """
    GET /model-info
    Returns information about the document classifier model.
    """
    return jsonify({
        'model': 'EfficientNetB0',
        'device': device,
        'classes': MODEL_CONFIG['class_names'],
        'image_size': MODEL_CONFIG['image_size'],
        'loaded': loaded_model is not None
    }), 200


# ==================== Initialization ====================

def init_document_classifier():
    """
    Initialize the document classifier module.
    Call this when the Flask app starts up.
    """
    global loaded_model
    
    print("\n📦 Initializing Document Classifier Module...")
    print(f"   Device: {device}")
    print(f"   Model checkpoint: {MODEL_CONFIG['checkpoint_path']}")
    print(f"   Classes: {MODEL_CONFIG['class_names']}")
    
    # Load the model
    model = load_document_classifier_model()
    
    if model is None:
        print("⚠️  Warning: Document classifier model failed to load")
        return False
    
    print("✓ Document Classifier Module initialized successfully\n")
    return True
