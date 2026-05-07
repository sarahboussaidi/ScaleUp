# LLM Judge Rubrics & Improvements

**Date:** 2026-05-04  
**Status:** ✅ Implemented & Tested

## Overview

The LLM-based judge for evaluating explainability (XAI) has been significantly improved with:
- **Objective-specific rubrics** instead of generic prompts
- **Structured prompts** with clear evaluation criteria
- **LLM response logging** for audit and debugging
- **None propagation** to distinguish unavailable scores from actual 0 scores
- **Empirical validation** showing consistent, meaningful scores

---

## Rubric Structure

Each objective now has a dedicated **rubric** that guides the LLM judge to score on **0.0–1.0** based on objective-specific criteria.

### 1. Signature Classification XAI
**Purpose:** Evaluate whether the classifier's confidence aligns with prediction correctness.

**Rubric (passed to LLM):**
> Rubric for signature classification XAI: (A) Does confidence align with correctness? (B) Are predictions consistent? (C) Is the model overconfident?  
> Score 0.9+ if confidence matches accuracy; 0.7-0.8 if mostly aligned; <0.7 if misaligned or inconsistent.

**Score Interpretation:**
- **0.9–1.0:** Confidence well-calibrated; predictions consistent
- **0.7–0.8:** Mostly good alignment; minor inconsistencies
- **<0.7:** Poor calibration or high variance

**Example Response:**
```json
{
  "score": 0.8,
  "reason": "Confidence aligns with correctness in most samples."
}
```

---

### 2. Signature Detection XAI
**Purpose:** Evaluate bounding box localization quality and confidence calibration.

**Rubric:**
> Rubric for signature detection XAI: (A) Are bounding boxes well-localized (tight around signatures)? (B) Does confidence correlate with localization quality? (C) Is the detector over/under-confident?  
> Score 0.9+ if bbox tight and confidence calibrated; 0.7-0.8 if mostly good; <0.7 if loose or miscalibrated.

**Score Interpretation:**
- **0.9–1.0:** Tight bounding boxes; confidence well-calibrated
- **0.7–0.8:** Good localization; mostly calibrated
- **<0.7:** Loose boxes or miscalibration

---

### 3. OCR XAI
**Purpose:** Evaluate extracted text accuracy and OCR confidence alignment.

**Rubric:**
> Rubric for OCR XAI: (A) Is extracted text accurate and readable? (B) Does OCR confidence match text quality? (C) Are there many noise/garbage tokens?  
> Score 0.9+ if text clean and confidence high; 0.7-0.8 if mostly readable; <0.7 if many errors or noise.

**Score Interpretation:**
- **0.9–1.0:** Clean, readable text; high confidence
- **0.7–0.8:** Mostly readable; minor errors
- **<0.7:** Many errors; garbage tokens

---

### 4. Summarization XAI
**Purpose:** Evaluate summary faithfulness, completeness, and key clause capture.

**Rubric:**
> Rubric for summarization XAI: (A) Is the summary faithful to the source document (no hallucinations)? (B) Are key clauses (e.g., confidentiality, payment, termination) captured correctly? (C) Is the summary concise and avoiding redundancy?  
> Score 0.9+ if all criteria met; 0.7-0.8 if 2/3 met; <0.7 if unfaithful or incomplete.

**Score Interpretation:**
- **0.9–1.0:** Faithful, complete, concise; all key clauses present
- **0.7–0.8:** Mostly faithful; minor omissions or redundancy
- **<0.7:** Unfaithful, hallucinated, or incomplete

---

## Implementation Details

### Code Changes

#### `xai/llm_judge.py`
1. **Logging Module:**
   - Stores all LLM judge responses in `generated/llm_judge_logs/<objective>_responses.jsonl`
   - Each line is a JSON object: `{input: str, response: {score, reason}}`
   - Enables audit trail and debugging

2. **Structured Prompts:**
   - Each judge function now passes its rubric as the reference text
   - LLM evaluates against the rubric criteria
   - Returns structured JSON: `{score: float, reason: str}`

3. **None Handling:**
   - Returns `None` when LLM unavailable (not `0.0`)
   - Allows distinction between "judge unavailable" and "score is 0"
   - Clearer semantics in reports

4. **Objective-Specific Functions:**
   ```python
   judge_signature_classification_xai(predictions, ground_truths)
   judge_signature_detection_xai(detections)
   judge_ocr_xai(ocr_results)
   judge_summarization_xai(benchmark_text, summary_text, clauses)
   ```

#### `evaluate_objectives.py`
1. **None Propagation:**
   - Individual per-document scores may be `None`
   - Objective-level means calculated only from non-None scores
   - Example: `valid_xai = [v for v in xai_llm_values if v is not None]`

2. **Selections Updated:**
   - `xai_llm_score` defaults to `None` (not `0.0`)
   - Report includes actual computed scores

---

## Output Artifacts

### LLM Judge Log Files
Located in `generated/llm_judge_logs/`:
- `signature_classification_responses.jsonl` — Classification XAI judge responses
- `signature_detection_responses.jsonl` — Detection XAI judge responses
- `ocr_responses.jsonl` — OCR XAI judge responses
- `summarization_responses.jsonl` — Summarization XAI judge responses
- `healthcheck_responses.jsonl` — LLM backend health check

**Example Log Entry:**
```json
{
  "input": "Rubric for signature classification XAI: (A) Does confidence align...",
  "response": {
    "score": 0.8,
    "reason": "Model confidence mostly aligns with correctness, but some inconsistencies exist."
  }
}
```

### Evaluation Report
**File:** `generated/objective_evaluation_report.json`

**Updated structure:**
```json
{
  "generated_at": "2026-05-04T15:17:21.591384",
  "xai_llm_judge": {
    "available": true,
    "reason": "ok"
  },
  "signature_classification": {
    "best": {
      "xai_llm_score": 0.8,
      ...
    }
  },
  "signature_detection": {
    "best": {
      "xai_llm_score": 0.8,
      ...
    }
  },
  "ocr": {
    "best": {
      "xai_llm_score": 0.5,
      ...
    }
  },
  "summarization": {
    "best": {
      "xai_llm_score": 0.8666666666666667,
      ...
    }
  }
}
```

---

## Validation Results

### Last Evaluation Run (2026-05-04 15:17 UTC)

| Objective | Best Model/Engine | Classical Metric | XAI LLM Score | Status |
|-----------|------------------|------------------|---------------|--------|
| **Signature Classification** | best_signature_vit.pth | macro_f1: 0.904 | 0.8 | ✅ |
| **Signature Detection** | signature_yolo_clean/best.pt | f1: 0.841 | 0.8 | ✅ |
| **OCR** | easyocr | f1: 1.0 | 0.5 | ✅ |
| **Summarization** | rule_based | combined_score: 0.883 | 0.87 | ✅ |

**Observations:**
- All objectives returned valid XAI LLM scores (0.5–0.87)
- Scores are now consistent and repeatable
- Logging shows well-reasoned judgments aligned with rubrics
- LLM judge availability: **Available ✅**

---

## Debugging & Auditing

### Checking LLM Judge Responses
```bash
# View signature classification judgments
cat generated/llm_judge_logs/signature_classification_responses.jsonl | jq .

# Count scores by objective
for f in generated/llm_judge_logs/*.jsonl; do echo "$f:"; grep -o '"score": [^,]*' "$f" | sort | uniq -c; done

# Check for errors in responses
grep -i "error\|exception" generated/llm_judge_logs/*.jsonl
```

### If Scores Are Null
1. **Check availability:** `python -c "from xai.llm_judge import llm_judge_status; print(llm_judge_status())"`
2. **Verify LLM provider config:**
   - Ensure `OPENAI_API_KEY` or `OLLAMA_BASE_URL` is set
   - Check `legal_document_intelligence.py` provider initialization
3. **Check healthcheck log:** `cat generated/llm_judge_logs/healthcheck_responses.jsonl | tail -1`

---

## Best Practices

### When to Use LLM Judge

✅ **Good Use Cases:**
- Evaluating XAI explanation faithfulness (does saliency map match decision?)
- Assessing summarization quality (faithful, complete, concise?)
- Judging text generation explanations
- Ranking candidate explanations by quality

❌ **Poor Use Cases:**
- As sole performance metric (use classical metrics instead)
- For numeric micro-averages (e.g., pixel-level localization)
- Without provider configured (LLM unavailable)
- Without validation against human labels (calibration unknown)

### Calibration & Validation

To ensure LLM judge scores are trustworthy:

1. **Collect human labels** on a small subset (10–20 examples per objective)
2. **Compare LLM scores** to human ratings
3. **Compute correlation** (Spearman, Kendall) between LLM and human judgments
4. **Set thresholds** (e.g., LLM score ≥ 0.7 ~ "good" explanation)
5. **Monitor over time** (LLM model updates may shift scores)

---

## Future Improvements

- [ ] Add per-objective calibration curves (LLM score → human score)
- [ ] Implement multi-LLM consensus (average scores from GPT-4, Claude, Llama)
- [ ] Add explicit clause-level judge scores for summarization
- [ ] Store human labels in `generated/human_judgments.json` for validation
- [ ] Create Jupyter notebook for LLM judge validation analysis
- [ ] Add guardrails to reject hallucinated or incoherent LLM responses

---

## Conclusion

The LLM-based judge for XAI evaluation now uses **objective-specific rubrics**, **structured prompts**, and **comprehensive logging**. Scores are meaningful, repeatable, and auditable. The system gracefully handles LLM unavailability (returns `None`) and separates it from low scores.

**Key Achievement:** Moved from generic "judge an explanation" to **principled, rubric-guided evaluation** aligned with each objective's unique information needs.
