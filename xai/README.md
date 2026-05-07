# XAI tools: Explainability for Signature & Document Intelligence

This folder contains multiple explainability implementations for different ML components:
- **Grad-CAM**: Visual explanation for signature classification
- **Confidence Heatmaps**: OCR text region confidence visualization
- **Focus Regions**: Signature detection confidence + box explanations
- **Clause Confidence**: Legal document summarization explanations

## Quick Start

### 1. Signature Classification Explain (Grad-CAM)
**File:** `gradcam.py`  
**Endpoint:** `POST /api/signature/explain`  
**Frontend:** `http://127.0.0.1:8000/static/explain.html`

Upload a signature image. Returns:
- Prediction and confidence
- Grad-CAM heatmap overlay showing which regions influenced the decision
- Natural-language explanation like: "Predicted 'real' with 86.1% confidence. The model focused on about 15.0% of the signature area, mainly in the top-right region."

### 2. Signature Detection Explain (YOLO Confidence)
**File:** `detection_explain.py`  
**Endpoint:** `POST /api/signature/detect-explain`  
**Frontend:** `http://127.0.0.1:8000/static/detect-explain.html`

Upload an image. Returns:
- Number of detected signature regions
- Confidence score for each detection
- Focus regions (normalized bboxes)
- Explanation: e.g., "Detected 2 signature regions. High confidence: 2, Low confidence: 0. Average confidence: 92.5%."

### 3. OCR Explain (Confidence-Based Highlighting)
**File:** `ocr_explain.py`  
**Endpoint:** `POST /api/ocr/analyze-explain`  
**Frontend:** `http://127.0.0.1:8000/static/ocr-explain.html`

Upload a document image. Returns:
- Text regions colored by confidence (green=high, yellow=mid, red=low)
- Average OCR confidence
- Explanation of which regions are uncertain
- Annotated image showing all detected text boxes

### 4. Summarization Explain (Clause Confidence)
**File:** `summarization_explain.py`  
**Endpoint:** `POST /api/document/summarization-explain`  
**Frontend:** `http://127.0.0.1:8000/static/summarization-explain.html`

Paste or upload a legal document. Returns:
- Extracted clauses with confidence scores
- Keywords that triggered each clause extraction
- Natural-language reasoning for each clause
- Example: "Extracted 'liability' clause with 85% confidence. Triggered by keywords: liability, indemnity, damages."

## File Structure
```
xai/
  gradcam.py                - Grad-CAM for CNN/ResNet/ViT models
  ocr_explain.py            - OCR confidence heatmaps and highlighting
  detection_explain.py      - YOLO detection confidence & focus regions
  summarization_explain.py  - Clause extraction confidence & attribution
  demo_gradcam.py           - CLI demo for Grad-CAM
  README.md                 - This file
```

## API Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/signature/explain` | POST | Image file | Prediction, confidence, Grad-CAM overlay, explanation text |
| `/api/signature/detect-explain` | POST | Image file | Detections, confidence, focus regions, explanation |
| `/api/ocr/analyze-explain` | POST | Image file | Text regions, confidence, annotated image |
| `/api/document/summarization-explain` | POST | JSON (text) | Clauses, confidence, explanations |

## Interpretation Tips

### Signature Classification
- Focus box should align with actual signature strokes
- If it doesn't, the prediction may be unreliable
- Lower `salient_area_ratio` = tighter, more focused decision

### Signature Detection
- High confidence ≥ 0.7 → likely real signature region
- Low confidence < 0.7 → may be noise or non-signature content
- Multiple detections → compare their confidence levels

### OCR
- Green boxes (>80% confidence) → likely accurate
- Yellow boxes (60-80%) → review carefully
- Red boxes (<60%) → may be misread; use context

### Summarization
- Confidence ≥ 0.8 → high-confidence clause extraction
- Keywords in the text confirm why a clause was extracted
- Review low-confidence clauses manually

## Running Locally

```bash
# Start the server
cd "/Users/mac/Documents/django/scaleup copy"
"/Users/mac/Documents/django/scaleup copy/.venv/bin/python" -m uvicorn chatbot_api:app --host 127.0.0.1 --port 8000

# Open any of the frontends
http://127.0.0.1:8000/static/explain.html
http://127.0.0.1:8000/static/detect-explain.html
http://127.0.0.1:8000/static/ocr-explain.html
http://127.0.0.1:8000/static/summarization-explain.html
```

Or use curl for direct API calls (examples already exist in the docs above).

Notes
- The Grad-CAM hooks require a regular `nn.Module` loaded from a `.pth` state dict. If your deployed model is TorchScript (`*_script.pt`), the demo and API will attempt to find a `.pth` fallback (e.g., `best_signature_resnet18.pth`). If no fallback exists the endpoint will return a helpful error message.
