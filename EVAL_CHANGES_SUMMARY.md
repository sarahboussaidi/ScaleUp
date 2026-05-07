# Multi-Objective XAI LLM Judge Integration - Summary

**Date Generated:** May 4, 2026  
**Status:** ✓ Completed

## Objective

Expand LLM judge evaluation from summarization only to cover all 4 project objectives:
- Signature Classification
- Signature Detection  
- OCR
- Summarization

## Implementation

### 1. xai/llm_judge.py (Extended)

Added 4 objective-specific judge functions:

- **`judge_signature_classification_xai(predictions, ground_truths) → float`**
  - Evaluates Grad-CAM explanation quality for signature classification
  - Aggregates sampled predictions into one compact LLM prompt
  - Returns 0-1 confidence score

- **`judge_signature_detection_xai(detections) → float`**
  - Evaluates detection confidence and bounding box explanations
  - Samples up to 10 detections for efficient LLM judgment
  - Returns 0-1 confidence score

- **`judge_ocr_xai(ocr_results) → float`**
  - Evaluates OCR confidence explanations
  - Aggregates text/confidence pairs into summary prompt
  - Returns 0-1 confidence score

- **`judge_summarization_xai(benchmark_text, summary_text, clauses) → float`**
  - Evaluates clause-level keyword/confidence explanations
  - Uses existing `judge_explanation()` base function
  - Returns 0-1 confidence score

- **`llm_judge_status() → Dict`**
  - Reports whether LLM backend is available for judging
  - Includes status reason (e.g., "llm_judge_unavailable" if offline)

### 2. evaluate_objectives.py (Updated)

Modified evaluation functions to include XAI LLM judge scores:

- **`_evaluate_signature_classification()`**
  - Collects predictions for all samples
  - Calls `judge_signature_classification_xai()`
  - Stores `xai_llm_score` in metrics

- **`_evaluate_signature_detection()`**
  - Creates synthetic detection explanations per model
  - Calls `judge_signature_detection_xai()`
  - Stores `xai_llm_score` in metrics

- **`_evaluate_ocr()`**
  - Aggregates OCR engine outputs per image report
  - Calls `judge_ocr_xai()` per engine
  - Stores `xai_llm_score` in metrics

- **`_evaluate_summarization()`** (already implemented)
  - Calls `judge_summarization_xai()` for each benchmark
  - Stores per-document `xai_llm_score`
  - Uses aggregated score in combined_score weighting

- **`build_report()`**
  - Adds `xai_llm_judge` metadata to report (status + reason)
  - Includes `xai_llm_score` in selections for all 4 objectives

### 3. static/evaluation.html (Updated Dashboard)

Changed from single "XAI LLM Judge" metric to 4 objective-specific cards:

```
Signature Macro F1 | Signature XAI LLM Judge
Detection F1 | Detection XAI LLM Judge
OCR F1 | OCR XAI LLM Judge
Summarization Score | Summarization XAI LLM Judge
ROUGE-L F | Summary Term Recall
```

Added status line:
```
Loaded report generated at {timestamp} | LLM Judge: available/unavailable ({reason})
```

## Report Structure

**JSON Output** (`objective_evaluation_report.json`):

```json
{
  "generated_at": "2026-05-04T13:40:54.257178",
  "xai_llm_judge": {
    "available": false,
    "reason": "llm_judge_unavailable"
  },
  "signature_classification": {
    "best": { "xai_llm_score": 0.0, ... },
    "candidates": [...]
  },
  "signature_detection": {
    "best": { "xai_llm_score": 0.0, ... },
    "candidates": [...]
  },
  "ocr": {
    "best": { "xai_llm_score": 0.0, ... },
    "candidates": [...]
  },
  "summarization": {
    "best": { "xai_llm_score": 0.0, ... },
    "candidates": [...]
  },
  "selections": {
    "signature_classification": { "xai_llm_score": 0.0, ... },
    "signature_detection": { "xai_llm_score": 0.0, ... },
    "ocr": { "xai_llm_score": 0.0, ... },
    "summarization": { "xai_llm_score": 0.0, ... }
  }
}
```

## Evaluation Workflow

1. **Run evaluation:**
   ```bash
   cd "/Users/mac/Documents/django/scaleup copy"
   source .venv/bin/activate
   python evaluate_objectives.py
   ```

2. **Output files generated:**
   - `/generated/objective_evaluation_report.json` — Full metrics + LLM judge scores
   - `/generated/objective_selections.json` — Best model/engine selections with XAI scores

3. **View dashboard:**
   - Open `/static/evaluation.html` in browser
   - Shows all 4 objectives' traditional metrics + XAI LLM judge scores
   - Status line shows whether LLM backend is available

## Notes on LLM Judge Availability

- **If unavailable:** All `xai_llm_score` values return 0.0
- **Reason:** OpenAI API key or Ollama backend not configured
- **To enable:** Set environment variables:
  ```bash
  export OPENAI_API_KEY="sk-..."
  export OPENAI_MODEL="gpt-4o-mini"
  # OR
  export OLLAMA_BASE_URL="http://localhost:11434"
  export OLLAMA_MODEL="llama2"
  ```
- **Dashboard displays status:** "LLM Judge: available/unavailable (reason)"

## Coverage Summary

| Objective | Traditional Metric | ROUGE | XAI Judge |
|-----------|-------------------|-------|-----------|
| Signature Classification | macro_f1 | — | ✓ |
| Signature Detection | f1, map50, map50_95 | — | ✓ |
| OCR | consensus_f1 | — | ✓ |
| Summarization | combined_score | ✓ | ✓ |

**Key Achievement:** Each of the 4 objectives now has an LLM judge score that evaluates the quality of explanations specific to that objective's XAI approach (Grad-CAM, detection confidence, OCR confidence, clause extraction).
