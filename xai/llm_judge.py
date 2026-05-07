from typing import Any, Dict, List, Optional
import json
from pathlib import Path

from legal_document_intelligence import LegalDocumentIntelligence

# Logging directory for LLM responses
JUDGE_LOG_DIR = Path(__file__).parent.parent / "generated" / "llm_judge_logs"
JUDGE_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log_judge_response(objective: str, input_summary: str, response: Dict[str, Any]) -> None:
    """Store LLM judge response for audit and debugging."""
    try:
        log_file = JUDGE_LOG_DIR / f"{objective}_responses.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({"input": input_summary[:200], "response": response}, default=str) + "\n")
    except Exception:
        pass


def judge_explanation(reference_text: str, explanation_text: str, clauses: Optional[List[Dict[str, Any]]] = None, objective: str = "generic") -> Dict[str, Any]:
    """Use the configured LLM to judge an explanation with objective-specific rubric.

    Returns a dict with keys: score (0-1 float) and reason (short string).
    """
    try:
        intel = LegalDocumentIntelligence()
        payload = {
            "task": "judge_xai_explanation",
            "reference": reference_text,
            "explanation": explanation_text,
            "clauses": clauses or [],
            "instructions": (
                "You are an expert evaluator. Rate the explanation on a 0-1 scale based on: "
                "(A) Faithfulness to the model's decision, (B) Clarity and specificity, (C) Completeness. "
                "Return JSON ONLY with keys: score (float, 0.0-1.0) and reason (one sentence max, <50 chars). "
                "Do NOT include markdown, extra text, or keys beyond score and reason."
            ),
        }
        resp = intel._invoke_ai(payload)
        # Expect resp to be a dict with score and reason
        score = float(resp.get("score", 0.0)) if resp else 0.0
        reason = str(resp.get("reason", "")) if resp else ""
        # normalize to 0-1
        if score > 1.0:
            score = 1.0
        if score < 0.0:
            score = 0.0
        result = {"score": float(score), "reason": reason}
        _log_judge_response(objective, reference_text[:100] + "..." + explanation_text[:100], result)
        return result
    except Exception as e:
        _log_judge_response(objective, reference_text[:100] if reference_text else "", {"error": str(e)})
        return {"score": None, "reason": "llm_judge_unavailable"}


def judge_signature_classification_xai(predictions: List[Dict[str, Any]], ground_truths: List[int]) -> float:
    """Judge signature classification explanation quality with structured rubric.
    
    Rubric: Does the model's confidence align with accuracy? Are explanations specific to fake/real traits?
    Score 0.9-1.0: High agreement, clear reasoning
    Score 0.7-0.8: Good agreement, reasonable explanations
    Score <0.7: Poor agreement or vague explanations
    """
    if not predictions:
        return None

    try:
        sampled = predictions[:10]
        sample_lines = []
        total = len(predictions)
        agreement = 0
        mean_conf = 0.0
        for item in sampled:
            pred = item.get("pred", -1)
            truth = item.get("true", -1)
            conf = float(item.get("confidence", 0.0) or 0.0)
            sample_lines.append(f"pred={pred}, truth={truth}, conf={conf:.3f}")

        for item in predictions:
            pred = int(item.get("pred", -1))
            truth = int(item.get("true", -1))
            conf = float(item.get("confidence", 0.0) or 0.0)
            if pred == truth:
                agreement += 1
            mean_conf += conf

        accuracy = agreement / max(total, 1)
        mean_conf = mean_conf / max(total, 1)

        explanation = (
            f"Signature fake/real classification: {len(predictions)} samples, accuracy={accuracy:.1%}, mean_confidence={mean_conf:.3f}. "
            f"Samples (pred, truth, conf): {'; '.join(sample_lines)}. "
            "Does model confidence correlate with prediction correctness?"
        )
        
        rubric = (
            "Rubric for signature classification XAI: (A) Does confidence align with correctness? "
            "(B) Are predictions consistent? (C) Is the model overconfident? "
            "Score 0.9+ if confidence matches accuracy; 0.7-0.8 if mostly aligned; <0.7 if misaligned or inconsistent."
        )
        
        judgment = judge_explanation(rubric, explanation, objective="signature_classification")
        score = judgment.get("score")
        if score is None:
            return None
        return float(score)
    except Exception:
        return None


def judge_signature_detection_xai(detections: List[Dict[str, Any]]) -> float:
    """Judge detection explanation quality with structured rubric.
    
    Rubric: Are bounding boxes well-localized? Do confidence scores reflect detection quality?
    Score 0.9-1.0: High precision localization, confidence aligns with F1
    Score 0.7-0.8: Good localization, mostly aligned
    Score <0.7: Poor localization or confidence miscalibration
    """
    if not detections:
        return None

    try:
        sampled = detections[:10]
        sample_lines = []
        mean_conf = sum(float(det.get("confidence", 0.0)) for det in detections) / max(len(detections), 1)
        
        for det in sampled:
            conf = float(det.get("confidence", 0.0))
            bbox = det.get("bbox", [])
            sample_lines.append(f"conf={conf:.3f}, bbox={bbox}")

        explanation = (
            f"Signature detection: {len(detections)} detections, mean_confidence={mean_conf:.3f}. "
            f"Samples (conf, bbox): {'; '.join(sample_lines)}. "
            "Are bounding boxes tight? Does confidence reflect detection precision?"
        )
        
        rubric = (
            "Rubric for signature detection XAI: (A) Are bounding boxes well-localized (tight around signatures)? "
            "(B) Does confidence correlate with localization quality? (C) Is the detector over/under-confident? "
            "Score 0.9+ if bbox tight and confidence calibrated; 0.7-0.8 if mostly good; <0.7 if loose or miscalibrated."
        )
        
        judgment = judge_explanation(rubric, explanation, objective="signature_detection")
        score = judgment.get("score")
        if score is None:
            return None
        return float(score)
    except Exception:
        return None


def judge_ocr_xai(ocr_results: List[Dict[str, Any]]) -> float:
    """Judge OCR explanation quality with structured rubric.
    
    Rubric: Are OCR tokens accurate? Is confidence aligned with text quality?
    Score 0.9-1.0: High accuracy, confidence calibrated, clean output
    Score 0.7-0.8: Good accuracy, mostly clean
    Score <0.7: Poor accuracy or lots of noise
    """
    if not ocr_results:
        return None

    try:
        sampled = ocr_results[:15]
        sample_lines = []
        mean_conf = sum(float(item.get("confidence", item.get("conf", 0.0))) for item in ocr_results) / max(len(ocr_results), 1)
        
        for item in sampled:
            text = str(item.get("text", ""))[:30]
            conf = float(item.get("confidence", item.get("conf", 0.0)))
            sample_lines.append(f"text='{text}', conf={conf:.3f}")

        explanation = (
            f"OCR extraction: {len(ocr_results)} tokens, mean_confidence={mean_conf:.3f}. "
            f"Samples (text, conf): {'; '.join(sample_lines)}. "
            "Are extracted words readable? Does confidence reflect accuracy?"
        )
        
        rubric = (
            "Rubric for OCR XAI: (A) Is extracted text accurate and readable? "
            "(B) Does OCR confidence match text quality? (C) Are there many noise/garbage tokens? "
            "Score 0.9+ if text clean and confidence high; 0.7-0.8 if mostly readable; <0.7 if many errors or noise."
        )
        
        judgment = judge_explanation(rubric, explanation, objective="ocr")
        score = judgment.get("score")
        if score is None:
            return None
        return float(score)
    except Exception:
        return None


def judge_summarization_xai(benchmark_text: str, summary_text: str, clauses: Optional[List[Dict[str, Any]]] = None) -> float:
    """Judge the quality of summarization explanations (clause confidence and highlights) with structured rubric.
    
    Rubric: Is the summary faithful to the source? Does it capture key clauses and constraints?
    Score 0.9-1.0: Faithful, concise, complete key clauses
    Score 0.7-0.8: Mostly faithful, minor omissions
    Score <0.7: Unfaithful, incomplete, or hallucinated
    """
    try:
        rubric = (
            "Rubric for summarization XAI: (A) Is the summary faithful to the source document (no hallucinations)? "
            "(B) Are key clauses (e.g., confidentiality, payment, termination) captured correctly? "
            "(C) Is the summary concise and avoiding redundancy? "
            "Score 0.9+ if all criteria met; 0.7-0.8 if 2/3 met; <0.7 if unfaithful or incomplete."
        )
        judgment = judge_explanation(rubric, summary_text, clauses, objective="summarization")
        score = judgment.get("score")
        if score is None:
            return None
        return float(score)
    except Exception:
        return None


def llm_judge_status() -> Dict[str, Any]:
    """Return availability details for LLM-based judging."""
    result = judge_explanation("healthcheck", "healthcheck", objective="healthcheck")
    reason = str(result.get("reason", ""))
    available = result.get("score") is not None
    return {
        "available": available,
        "reason": "ok" if available else "llm_judge_unavailable",
    }
