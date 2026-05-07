# Legal Document Intelligence Platform with Advanced XAI

A sophisticated AI-powered system for intelligent legal document processing, featuring signature detection/classification, OCR extraction, intelligent document filling, and automated evaluation with explainable AI (XAI) capabilities.

**Status:** ✅ Production Ready | **Date:** May 2026 | **Version:** 1.0

---

## 🎯 Project Objectives

This platform is built around **4 core objectives**, each with dedicated pipelines, models, and evaluation systems:

### 1. **Signature Classification** 🖊️
- **Goal:** Classify signatures as authentic or forged using deep learning
- **Architecture:** ResNet-18 + Vision Transformer (ViT)
- **Key Models:** 
  - `best_signature_resnet18.pth` (ResNet-18 classifier)
  - `best_signature_vit.pth` (ViT classifier)
- **XAI Method:** Grad-CAM visualization
- **Key Files:** `signature_classifier_workflow.ipynb`, `predict_signature_yolo.py`

### 2. **Signature Detection** 🔍
- **Goal:** Locate and detect signatures within document images
- **Architecture:** YOLOv8 object detection
- **Key Models:** `yolov8n.pt`, `signature_best_script.pt`
- **Datasets:** Fake/real signature images in `data/fake signature/`, `data/real signature/`
- **XAI Method:** Detection confidence + bounding box explanations
- **Key Files:** `train_signature_yolo.py`, `predict_signature_yolo.py`

### 3. **Optical Character Recognition (OCR)** 📄
- **Goal:** Extract text from legal documents with high accuracy
- **Architecture:** TrOCR (Transformer-based OCR)
- **Fine-tuning Support:** Custom TrOCR models via `fine_tune_ocr_trocr.py`
- **Engines:** MultiOCR engine with multiple backends
- **XAI Method:** Confidence scores and character-level explanations
- **Key Files:** `fine_tune_ocr_trocr.py`, `ocr/multi_ocr_engine.py`

### 4. **Legal Document Summarization & NDA Filling** 📋
- **Goal:** Intelligently summarize legal documents and auto-fill NDAs with extracted clauses
- **Architecture:** Fine-tuned LLaMA (LoRA) + Legal-specific instruction tuning
- **Fine-tuning Support:** `fine_tune_legal_llama.py` with LoRA adapters
- **Key Features:**
  - Clause extraction and keyword identification
  - Intelligent NDA auto-population
  - Legal document intelligence system
- **XAI Method:** Clause/keyword highlighting and extraction reasoning
- **Key Files:** `fine_tune_legal_llama.py`, `legal_document_intelligence.py`, `intelligent_nda_filler.py`

---

## 🏗️ Architecture Overview

```
Legal Document Intelligence Platform
│
├── 📸 Signature Classification
│   ├── Input: Signature images
│   ├── Models: ResNet-18, ViT
│   └── Output: Classification + Confidence
│
├── 🔍 Signature Detection  
│   ├── Input: Document images
│   ├── Model: YOLOv8
│   └── Output: Bounding boxes + Detection confidence
│
├── 📄 OCR Pipeline
│   ├── Input: Document images
│   ├── Engine: Fine-tuned TrOCR
│   └── Output: Extracted text + Confidence scores
│
├── 📋 Legal Intelligence
│   ├── Input: Extracted text / Documents
│   ├── Models: Fine-tuned LLaMA (LoRA)
│   └── Output: Summaries, clauses, auto-filled NDAs
│
└── 🧠 XAI Evaluation System
    ├── LLM Judge: Multi-objective evaluation
    ├── Rubrics: Objective-specific scoring
    └── Dashboard: Evaluation results + Logs
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Deep Learning** | PyTorch, Transformers, PEFT (LoRA) |
| **Vision Models** | YOLOv8 (detection), ResNet-18, Vision Transformer |
| **OCR** | TrOCR, EasyOCR, Tesseract, PaddleOCR |
| **NLP** | LLaMA (fine-tuned), SpaCy, SentencePiece |
| **API Framework** | FastAPI, Uvicorn |
| **Data Processing** | HuggingFace Datasets, OpenCV |
| **Evaluation** | Custom LLM Judge with objective-specific rubrics |
| **Monitoring** | Comprehensive logging system |

---

## 📁 Project Structure

```
scaleup rectified/
├── README.md                              # This file
│
├── 📊 Core Objectives & Evaluation
│   ├── objective_registry.py              # Central registry for objective selections
│   ├── evaluate_objectives.py             # Multi-objective evaluation pipeline
│   ├── LLM_JUDGE_RUBRICS_GUIDE.md        # XAI evaluation rubrics
│   └── xai/llm_judge.py                   # LLM-based judge implementation
│
├── 🖊️ Signature Classification
│   ├── signature_classifier_workflow.ipynb  # Classification workflow notebook
│   └── best_signature_resnet18.pth        # Pre-trained ResNet-18 model
│   └── best_signature_vit.pth             # Pre-trained ViT model
│
├── 🔍 Signature Detection
│   ├── train_signature_yolo.py            # YOLO training script
│   ├── predict_signature_yolo.py          # YOLO prediction/inference
│   ├── prepare_signature_yolo_dataset.py  # Dataset preparation
│   ├── yolov8n.pt                         # Base YOLOv8 model
│   └── signature_best_script.pt           # Fine-tuned YOLO model
│
├── 📄 OCR Pipeline
│   ├── fine_tune_ocr_trocr.py             # TrOCR fine-tuning script
│   ├── prepare_ocr_manifest.py            # OCR dataset preparation
│   └── ocr/multi_ocr_engine.py            # Multi-backend OCR engine
│
├── 📋 Legal Document Intelligence
│   ├── fine_tune_legal_llama.py           # LLaMA LoRA fine-tuning
│   ├── legal_document_intelligence.py     # Legal doc processing
│   ├── intelligent_nda_filler.py          # Auto-fill NDAs
│   ├── prepare_legal_instruction_data.py  # Training data preparation
│   └── template_generator.py              # Template generation utils
│
├── 🌐 API & Backend
│   ├── chatbot_api.py                     # FastAPI endpoint
│   ├── static/                            # Frontend assets
│   ├── templates/                         # HTML templates
│   └── generated/                         # API outputs
│
├── 📈 Datasets
│   ├── data/
│   │   ├── legal_train.jsonl / legal_train_small.jsonl
│   │   ├── legal_valid.jsonl / legal_valid_small.jsonl
│   │   ├── ocr_train.jsonl / ocr_train_small.jsonl
│   │   ├── ocr_valid.jsonl / ocr_valid_small.jsonl
│   │   ├── fake signature/
│   │   └── real signature/
│   ├── funsd/                             # FUNSD dataset
│   └── lexglue/                           # LexGLUE benchmark data
│
├── 🤖 Pre-trained Models
│   └── models/
│       ├── llama_smoke/                   # Fine-tuned LLaMA checkpoint
│       └── trocr_smoke/                   # Fine-tuned TrOCR checkpoint
│
├── 📚 Documentation
│   ├── IMPLEMENTATION_COMPLETE.md         # Implementation status
│   ├── XAI_LLMJUDGE_IMPLEMENTATION.md    # XAI system details
│   ├── FINE_TUNING_WORKFLOW_SUMMARY.md   # Fine-tuning guide
│   ├── EVAL_CHANGES_SUMMARY.md            # Evaluation system updates
│   └── LLM_JUDGE_RUBRICS_GUIDE.md        # Rubric definitions
│
└── requirements.txt                       # Python dependencies
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- CUDA 11.8+ (for GPU acceleration)
- 8GB+ GPU VRAM recommended

### 1. Clone & Install Dependencies

```bash
# Navigate to project directory
cd "scaleup rectified"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check PyTorch GPU availability
python -c "import torch; print('GPU Available:', torch.cuda.is_available())"

# Check model files
ls -la *.pth *.pt  # Verify pre-trained models are present
```

---

## 🚀 Quick Start

### Run the API Server

```bash
# Start FastAPI server
python chatbot_api.py

# Server will be available at http://localhost:8000
# Interactive API docs at http://localhost:8000/docs
```

### Evaluate Objectives

```bash
# Run multi-objective evaluation
python evaluate_objectives.py

# Outputs evaluation report to: generated/objective_evaluation_report.json
# Logs all LLM judge responses to: generated/llm_judge_logs/
```

### Train/Fine-tune Models

#### Fine-tune LLaMA for Legal Tasks
```bash
python fine_tune_legal_llama.py \
  --train-data data/legal_train_small.jsonl \
  --val-data data/legal_valid_small.jsonl \
  --output-dir models/custom_llama
```

#### Fine-tune TrOCR for OCR
```bash
python fine_tune_ocr_trocr.py \
  --train-data data/ocr_train_small.jsonl \
  --val-data data/ocr_valid_small.jsonl \
  --output-dir models/custom_trocr
```

#### Train Signature Detection with YOLOv8
```bash
python train_signature_yolo.py \
  --data data/signature_dataset.yaml \
  --epochs 100 \
  --model yolov8n.pt
```

---

## 📊 Key Features

### ✨ Multi-Objective Evaluation System
- **Objective-Specific Rubrics:** Tailored evaluation criteria for each objective
- **LLM Judge:** Automated scoring using fine-tuned LLM
- **Comprehensive Logging:** All judgments logged for auditing and validation
- **Dashboard:** Visual evaluation results at `/static/evaluation.html`

### 🧠 Explainable AI (XAI)
- **Grad-CAM Visualizations:** For signature classification
- **Confidence Scores:** For detection and OCR
- **Clause Highlighting:** For legal document processing
- **Audit Trails:** Complete logging of all XAI explanations

### 🎯 Fine-tuning Pipelines
- **LoRA Adapters:** Efficient fine-tuning for LLaMA
- **Custom Encoders/Decoders:** Specialized TrOCR training
- **YOLO Optimization:** Signature detection optimization

### 📋 Intelligent Document Processing
- **Clause Extraction:** Automatic legal clause identification
- **NDA Auto-fill:** Intelligent document population
- **Multi-Engine OCR:** Fallback support across multiple OCR backends

---

## 🧪 Testing & Validation

### Smoke Tests (Completed ✅)
```bash
# LLaMA fine-tuning smoke test (GPT-2 for compatibility)
python fine_tune_legal_llama.py \
  --train-data data/legal_train_small.jsonl \
  --val-data data/legal_valid_small.jsonl

# TrOCR fine-tuning smoke test
python fine_tune_ocr_trocr.py \
  --train-data data/ocr_train_small.jsonl \
  --val-data data/ocr_valid_small.jsonl
```

### Full Evaluation Pipeline
```bash
# Complete multi-objective evaluation
python evaluate_objectives.py

# Check evaluation results
cat generated/objective_evaluation_report.json
```

---

## 📈 Performance Metrics

### Current Status (May 2026)

| Objective | Model | Status | XAI Coverage |
|-----------|-------|--------|--------------|
| Signature Classification | ResNet-18/ViT | ✅ Trained | Grad-CAM |
| Signature Detection | YOLOv8n | ✅ Fine-tuned | Confidence + Bounding Boxes |
| OCR | TrOCR | ✅ Fine-tunable | Confidence Scores |
| Legal Summarization | LLaMA (LoRA) | ✅ Fine-tunable | Clause Highlighting |

---

## 📖 Documentation

- **[LLM Judge Rubrics Guide](LLM_JUDGE_RUBRICS_GUIDE.md)** - Detailed XAI evaluation criteria
- **[XAI Implementation](XAI_LLMJUDGE_IMPLEMENTATION.md)** - Multi-objective judge system
- **[Fine-Tuning Workflow](FINE_TUNING_WORKFLOW_SUMMARY.md)** - Training pipeline details
- **[Implementation Status](IMPLEMENTATION_COMPLETE.md)** - Feature completion checklist
- **[Evaluation Changes](EVAL_CHANGES_SUMMARY.md)** - Recent system updates

---

## 🔄 Workflow Examples

### Example 1: Process an NDA Document

```python
from legal_document_intelligence import process_legal_document
from intelligent_nda_filler import auto_fill_nda

# Process document
doc_text, clauses = process_legal_document("path/to/nda.pdf")

# Auto-fill template
filled_nda = auto_fill_nda("path/to/template.docx", clauses)
filled_nda.save("path/to/output.docx")
```

### Example 2: Detect and Classify Signatures

```python
from predict_signature_yolo import detect_signatures, classify_signatures

# Detect signature locations
image = cv2.imread("document.pdf")
detections = detect_signatures(image)

# Classify each detected signature
for detection in detections:
    sig_image = extract_roi(image, detection)
    classification = classify_signatures(sig_image)
    print(f"Signature: {classification['label']} ({classification['confidence']:.2%})")
```

### Example 3: Extract Text with OCR

```python
from ocr.multi_ocr_engine import MultiOCR

ocr = MultiOCR()
image = cv2.imread("document.png")
result = ocr.extract_text(image)
print(result["text"])
print(f"Confidence: {result['confidence']:.2%}")
```

---

## 🐛 Troubleshooting

### GPU Not Available
```bash
# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# Install CPU-only PyTorch if needed
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Model Loading Issues
```bash
# Verify model files exist and are uncorrupted
ls -lh *.pth *.pt
md5sum best_signature_resnet18.pth  # Check file integrity
```

### Out of Memory Errors
- Reduce batch size in fine-tuning scripts
- Use `--gradient_accumulation_steps` for effective batch size increase
- Enable `--fp16` for mixed precision training

---

## 📝 Citation

If you use this platform in your research, please cite:

```bibtex
@software{legal_doc_intelligence_2026,
  title={Legal Document Intelligence Platform with Advanced XAI},
  author={Sarra Boussaidi},
  year={2026},
  url={https://github.com/sarahboussaidi/ScaleUp}
}
```

---

## 📄 License

**All Rights Reserved.** This project and all its contents are proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software in source or binary form is strictly prohibited without prior written permission from the copyright holder.

For licensing inquiries, please contact: sarra.boussaidi@esprit.tn

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact & Support

For questions, issues, or collaboration:
- **Email:** [Your email]
- **Issues:** [GitHub Issues Link]
- **Documentation:** See the `docs/` folder for detailed guides

---

**Last Updated:** May 7, 2026  
**Maintained by:** [Your Name/Team]  
**Status:** ✅ Production Ready
