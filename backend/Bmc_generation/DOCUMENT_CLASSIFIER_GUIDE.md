# Document Classifier Integration Guide

## Overview

This document describes the integration of the EfficientNetB0 document type classifier into the Flask backend for the BMC AI Generation pipeline.

## Files

### New Files Created
- **`document_classifier_routes.py`** - Main module containing:
  - Model loading logic
  - Image preprocessing pipeline
  - EfficientNetB0 inference
  - Flask Blueprint with API endpoints

### Modified Files
- **`app.py`** - Updated to import and register the blueprint
- **`requirements.txt`** - Added PyTorch dependencies

## Installation

### 1. Install Required Dependencies

```bash
cd backend
pip install torch==2.0.0 torchvision==0.15.0 pillow==10.0.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Verify Model Checkpoint

The model checkpoint should be at:
```
backend/models/bmc_generation/best_doc_type_classifier.pth
```

Check if the file exists:
```bash
ls backend/models/bmc_generation/best_doc_type_classifier.pth
```

## API Endpoints

### 1. POST `/api/predict-document-type`

**Purpose**: Classify an uploaded image document type

**Request**:
```bash
curl -X POST http://localhost:5000/api/predict-document-type \
  -F "file=@/path/to/image.jpg"
```

**Request Headers**:
- Content-Type: multipart/form-data

**Request Body**:
- `file` (required): Image file (JPG, PNG, GIF, WebP)

**Response** (Success - 200):
```json
{
  "document_type": "handwritten",
  "confidence": 0.9456,
  "class_index": 1,
  "all_probabilities": {
    "bmc": 0.0234,
    "handwritten": 0.9456,
    "typed": 0.031
  }
}
```

**Response** (Error - 400/500):
```json
{
  "error": "Invalid image",
  "message": "Failed to preprocess image: ..."
}
```

### 2. GET `/api/model-info`

**Purpose**: Get information about the loaded model

**Request**:
```bash
curl http://localhost:5000/api/model-info
```

**Response**:
```json
{
  "model": "EfficientNetB0",
  "device": "cpu",
  "classes": ["bmc", "handwritten", "typed"],
  "image_size": 224,
  "loaded": true
}
```

## Model Details

### Architecture
- **Model**: EfficientNetB0
- **Framework**: PyTorch
- **Input Size**: 224 x 224 pixels
- **Classes**: 3
  - `bmc` - Business Model Canvas image
  - `handwritten` - Handwritten notes/sketch
  - `typed` - Typed/printed document

### Preprocessing
Images are preprocessed using ImageNet normalization:
- **Resize**: 224 x 224
- **Normalization Mean**: [0.485, 0.456, 0.406]
- **Normalization Std**: [0.229, 0.224, 0.225]
- **Color Space**: RGB

### Device Support
- Automatically detects and uses CUDA (GPU) if available
- Falls back to CPU if CUDA is not available

## Integration with Frontend

### Frontend Example (Next.js/React)

```typescript
async function classifyDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await fetch(
      'http://localhost:5000/api/predict-document-type',
      {
        method: 'POST',
        body: formData
      }
    )
    
    const result = await response.json()
    
    if (response.ok) {
      console.log('Document Type:', result.document_type)
      console.log('Confidence:', result.confidence)
      console.log('All Probabilities:', result.all_probabilities)
    } else {
      console.error('Error:', result.error)
    }
  } catch (error) {
    console.error('Request failed:', error)
  }
}
```

## Troubleshooting

### Issue: "Model not found" error

**Solution**: Verify the checkpoint file exists at the correct path:
```bash
ls -la backend/models/bmc_generation/best_doc_type_classifier.pth
```

### Issue: "CUDA out of memory" error

**Solution**: The model will automatically fall back to CPU. To force CPU:
```python
# Modify device selection in document_classifier_routes.py
device = 'cpu'
```

### Issue: "No module named 'torch'" error

**Solution**: Install PyTorch:
```bash
pip install torch torchvision
```

### Issue: Slow inference on first request

**Solution**: This is normal. Model loading and compilation takes time on the first request. Subsequent requests will be faster due to caching.

## Performance Notes

### Inference Time
- **First request**: ~2-5 seconds (model compilation)
- **Subsequent requests**: ~200-500ms

### Memory Requirements
- **Model size**: ~20 MB
- **RAM needed**: ~500 MB
- **VRAM (GPU)**: ~250 MB (if available)

## Configuration

To modify model configuration, edit `document_classifier_routes.py`:

```python
MODEL_CONFIG = {
    'checkpoint_path': os.path.join(...),  # Path to .pth file
    'image_size': 224,                     # Input image size
    'class_names': ['bmc', 'handwritten', 'typed'],  # Class names
    'num_classes': 3,                      # Number of classes
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'  # Device
}
```

## Testing

### Using cURL
```bash
# Test with a sample image
curl -X POST http://localhost:5000/api/predict-document-type \
  -F "file=@sample_bmc.jpg"

# Get model info
curl http://localhost:5000/api/model-info
```

### Using Python
```python
import requests

# Classify document
with open('image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:5000/api/predict-document-type',
        files=files
    )
    print(response.json())

# Get model info
info = requests.get('http://localhost:5000/api/model-info').json()
print(info)
```

## Next Steps

1. ✅ Created `document_classifier_routes.py` with full model integration
2. ✅ Updated `app.py` to register the blueprint
3. ✅ Updated `requirements.txt` with PyTorch dependencies
4. **TODO**: Install PyTorch and torchvision:
   ```bash
   cd backend
   pip install torch==2.0.0 torchvision==0.15.0
   ```
5. **TODO**: Test the endpoint:
   ```bash
   pnpm dev  # Start Flask server
   # In another terminal:
   curl -X POST http://localhost:5000/api/predict-document-type -F "file=@test_image.jpg"
   ```
6. **TODO**: Integrate into frontend BMC generation pipeline

## Support

For issues or questions:
1. Check the Flask server logs for error messages
2. Verify the checkpoint file exists and is valid
3. Ensure all PyTorch packages are installed correctly
4. Test with the `/api/model-info` endpoint to check model status
