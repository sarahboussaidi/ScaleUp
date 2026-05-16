# Multimodal SRS Intelligence & Generation System

## Overview

This project is an end-to-end AI system for **Software Requirements Specification (SRS)** analysis, evaluation, improvement, and generation.

The system can work in two main modes:

1. **SRS Analysis Mode**  
   Analyze existing SRS documents, extract requirements, classify them, detect ambiguity, evaluate quality, and generate final reports.

2. **SRS Generation Mode**  
   Generate a complete professional SRS document from a user project description using **RAG + LLM generation**, then validate and explain the generated output.

The final system combines:

- Document Intelligence
- Natural Language Processing
- Computer Vision
- Deep Learning
- Multimodal Quality Scoring
- Explainable AI
- LLM-based Requirement Rewriting
- RAG-based SRS Generation
- Final Reporting

---

## Project Structure

```text
SRS Project/
│
├── srs-req-detection-project-2.ipynb
├── srs-req-detection-project-3.ipynb
├── srs-req-detection-project-4.ipynb
├── srs-req-detection-project-5.ipynb
│
├── README.md
│
└── outputs/
    ├── notebook_2_outputs/
    ├── notebook_3_outputs/
    ├── notebook_4_outputs/
    └── notebook_5_outputs/
```

---

## Main Objective

The main objective is to build an intelligent assistant capable of helping analysts, students, startups, or software teams to:

- Understand SRS documents.
- Extract functional and non-functional requirements.
- Detect ambiguity and low-quality requirements.
- Classify requirements automatically.
- Analyze document structure and page types.
- Explain model predictions using XAI.
- Rewrite weak requirements using an LLM.
- Generate a new professional SRS from a user prompt.
- Export final results as CSV, Markdown, HTML, DOCX, and reports.

---

## Notebooks Description

### Notebook 2 — Document Intelligence & Deep NLP

**Goal:**  
Transform existing SRS documents into structured requirement-level intelligence.

Main tasks:

- Load SRS documents and page images.
- Extract text from PDFs using PyMuPDF.
- Use OCR fallback with EasyOCR when needed.
- Align pages, text, images, and document metadata.
- Detect document structure, headings, sections, and TOC consistency.
- Extract requirement candidates.
- Train and apply deep NLP models:
  - DistilBERT for FR/NFR classification.
  - RoBERTa for NFR subtype classification.
  - RoBERTa for ambiguity detection.
- Apply LIME for text-based explainability.

Important outputs:

```text
c5_requirement_extraction_table.csv
c6_deep_fr_nfr_predictions.csv
c7_nfr_subtype_predictions.csv
c8_deep_ambiguity_predictions.csv
c8_document_ambiguity_summary.csv
c6_lime_model_based_xai_sample.csv
c7_lime_nfr_subtype_xai_sample.csv
c8_lime_ambiguity_xai_sample.csv
```

---

### Notebook 3 — Computer Vision Page Intelligence

**Goal:**  
Classify SRS page images into page types using both a custom CNN and a pretrained ResNet18 model.

Page classes:

```text
cover_page
toc_page
content_page
appendix_page
low_text_page
```

Main tasks:

- Load aligned page image dataset.
- Preprocess images with resizing and normalization.
- Apply data augmentation.
- Split data by document into train, validation, and test sets.
- Train a custom CNN from scratch.
- Fine-tune a pretrained ResNet18 model.
- Compare both models.
- Use Grad-CAM to explain ResNet18 predictions.
- Generate page-level and document-level vision outputs.

Important outputs:

```text
v3_custom_cnn_page_classifier.pt
v3_custom_cnn_test_predictions.csv
v4_resnet18_page_classifier.pt
v4_resnet18_test_predictions.csv
v5_cv_model_comparison.csv
v6_gradcam_xai_samples.csv
v7_page_vision_predictions.csv
v7_document_vision_summary.csv
```

Best model:

```text
Pretrained ResNet18
```

Reason:

ResNet18 achieved better performance than the custom CNN, especially on weighted F1, which is important because the dataset is imbalanced.

---

### Notebook 4 — Multimodal Quality Scoring, LLM Rewrite & Final Reports

**Goal:**  
Fuse NLP outputs and Computer Vision outputs to evaluate the quality of each requirement.

Main tasks:

- Merge NLP predictions from Notebook 2 with vision predictions from Notebook 3.
- Build multimodal quality signals:
  - ambiguity
  - vague language
  - numeric constraints
  - modal verbs
  - section context
  - page type
  - vision confidence
- Generate silver quality labels.
- Train a RoBERTa quality classifier.
- Compute final neuro-symbolic quality scores.
- Detect quality issues and recommendations.
- Rewrite weak requirements using Qwen2.5-Instruct.
- Validate rewritten requirements.
- Generate final document and requirement reports.

Important outputs:

```text
c9_multimodal_requirement_quality_scores.csv
c9_section_quality_summary.csv
c9_document_quality_summary.csv
c10_llm_requirement_rewrites.csv
c11_final_requirement_report.csv
c11_final_document_report.csv
c11_top_problematic_requirements.csv
c11_final_project_summary.txt
```

---

### Notebook 5 — Intelligent SRS Generation

**Goal:**  
Generate a complete professional SRS document from a user project prompt.

The user provides:

- Project title
- Author / prepared by
- Project description
- Functional needs
- Non-functional needs
- Target users
- Constraints

Main tasks:

- Load outputs from previous notebooks.
- Build a generation knowledge base from high-quality requirements and rewritten requirements.
- Use TF-IDF + cosine similarity for RAG retrieval.
- Retrieve relevant examples for each SRS section.
- Use Qwen2.5-1.5B-Instruct to generate the SRS section by section.
- Generate requirements, risks, assumptions, conclusion, and references.
- Validate generated requirements.
- Evaluate structure coverage and generation quality.
- Generate XAI reports:
  - RAG evidence XAI
  - Requirement quality XAI
  - Section-level XAI
  - Global XAI report
- Export the final SRS in multiple formats.

Important outputs:

```text
generated_srs.md
generated_srs.html
generated_srs.docx
generated_requirements.csv
generated_sections.csv
rag_references.csv
generation_summary.txt
evaluation_xai/
```

---

## Models Used

| Task | Model / Method |
|---|---|
| FR/NFR classification | DistilBERT |
| NFR subtype classification | RoBERTa-base |
| Ambiguity detection | RoBERTa-base |
| Page image classification baseline | Custom CNN |
| Page image classification final model | Pretrained ResNet18 |
| Requirement quality classifier | RoBERTa-base |
| Requirement rewriting | Qwen2.5-1.5B-Instruct |
| SRS generation | Qwen2.5-1.5B-Instruct + RAG |
| Text XAI | LIME |
| Vision XAI | Grad-CAM |
| Generation XAI | RAG evidence + quality explanations |

---

## Why RAG + LLM?

The LLM is used to generate professional natural language content.

However, an LLM alone may:

- hallucinate information,
- generate vague requirements,
- ignore SRS structure,
- produce requirements without traceability.

RAG is used to reduce these risks by retrieving high-quality examples from previous SRS analysis outputs.  
This makes generation more:

- contextual,
- grounded,
- explainable,
- reusable,
- aligned with real SRS examples.

---

## Explainability

The project includes several XAI layers:

| XAI Method | Used For |
|---|---|
| LIME | Explain FR/NFR, NFR subtype, and ambiguity predictions |
| Grad-CAM | Explain ResNet18 page classification |
| Quality issue explanations | Explain requirement quality scores |
| RAG evidence tracing | Explain which retrieved examples supported generated sections |
| Global XAI report | Explain generation strategy and final score |

---

## Evaluation Summary

The project evaluates the system at several levels:

### NLP Evaluation

- FR/NFR classification with DistilBERT.
- NFR subtype classification with RoBERTa.
- Ambiguity detection with RoBERTa.
- Metrics include accuracy, precision, recall, F1, macro F1, and weighted F1.

### Computer Vision Evaluation

- Custom CNN vs pretrained ResNet18.
- Metrics include accuracy, macro F1, weighted F1, precision, recall, confusion matrix, and learning curves.
- ResNet18 was selected as the best Computer Vision model.

### Multimodal Quality Evaluation

- Requirement-level quality score.
- Section-level quality summary.
- Document-level quality summary.
- Issue detection and recommendation generation.

### SRS Generation Evaluation

- RAG retrieval quality.
- Section coverage.
- Generated requirement quality.
- Final generation score.
- XAI reports.

---

## Key Results

| Component | Result |
|---|---|
| Extracted requirements | 3608 |
| Page images | 1212 |
| Documents analyzed | 24 |
| Best CV model | Pretrained ResNet18 |
| Generated SRS sections | 10 |
| Generated requirements | 144 |
| Generated requirement quality | Mostly strong / acceptable |
| Final generation label | GOOD_GENERATION |
| Deployment | TODO |

---

## Deployment Status

The current project is implemented and tested offline in Kaggle notebooks.

Deployment and monitoring are marked as **TODO**.

Future deployment work may include:

- Web interface for user prompts.
- API endpoint for SRS generation.
- Upload system for PDF/SRS documents.
- Model serving for NLP and CV models.
- Storage of generated SRS versions.
- Feedback collection from users.
- Monitoring of quality drift and confidence drift.

---

## How to Run

1. Open the notebooks in order:

```text
Notebook 2 → Notebook 3 → Notebook 4 → Notebook 5
```

2. Make sure the required datasets are attached in Kaggle.

3. Run each notebook and save the generated outputs.

4. Use the outputs of each notebook as inputs for the next one.

5. Final outputs are generated by Notebook 5.

---

## Final Pipeline

```text
SRS PDFs / Page Images / User Prompt
        ↓
Document Intelligence + OCR + Requirement Extraction
        ↓
Deep NLP Classification + Ambiguity Detection + XAI
        ↓
Computer Vision Page Classification + Grad-CAM
        ↓
Multimodal Quality Scoring
        ↓
LLM Requirement Rewriting
        ↓
RAG + LLM SRS Generation
        ↓
Evaluation + XAI Reports + Export
        ↓
Deployment & Monitoring TODO
```

---

## Author

Prepared by:

```text
Cyrine Mejri
```

Project:

```text
SRS REQ Detection / Multimodal SRS Intelligence & Generation
```

---

## Final Note

This project demonstrates a complete multimodal AI pipeline for Software Requirements Engineering.  
It combines NLP, Computer Vision, Deep Learning, XAI, RAG, LLM generation, validation, and reporting to support intelligent SRS analysis and generation.
