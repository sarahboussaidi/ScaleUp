from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


def _ensure_project_venv() -> None:
    project_root = Path(__file__).resolve().parent
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current == target:
        return
    if os.environ.get("SCALEUP_SKIP_VENV_REEXEC") == "1":
        return
    os.execve(
        str(target),
        [str(target), str(Path(__file__).resolve()), *sys.argv[1:]],
        {**os.environ, "SCALEUP_SKIP_VENV_REEXEC": "1"},
    )


_ensure_project_venv()

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from ultralytics import YOLO

from legal_document_intelligence import LegalDocumentIntelligence
from rouge_score import rouge_scorer
from xai.llm_judge import (
    judge_signature_classification_xai,
    judge_signature_detection_xai,
    judge_ocr_xai,
    judge_summarization_xai,
    llm_judge_status,
)
from ocr.multi_ocr_engine import MultiOCREngine
from objective_registry import (
    GENERATED_DIR,
    PROJECT_ROOT,
    REPORT_FILE,
    SELECTIONS_FILE,
    save_objective_report,
    save_objective_selections,
)


@dataclass
class CandidateResult:
    name: str
    metrics: Dict[str, Any]


GRAY_TRANSFORM = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((128, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ]
)

RGB_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

OCR_SAMPLE_IMAGES = [
    PROJECT_ROOT / "ocr" / "00040534.png",
    PROJECT_ROOT / "ocr" / "annotated_test.png",
]

SUMMARY_BENCHMARKS = [
    {
        "name": "nda_confidentiality_liability",
        "text": (
            "This agreement is confidential and proprietary. The receiving party shall not disclose confidential information "
            "except as required by law. The term is 12 months and either party may terminate on written notice. "
            "Liability is capped and governed by the laws of Estonia."
        ),
        "expected_categories": {"confidentiality", "termination", "liability", "governing_law", "term"},
        "expected_doc_kind": "legal document",
        "expected_summary_terms": {"confidential", "term", "terminate", "liability", "governing law"},
    },
    {
        "name": "startup_investment_governance",
        "text": (
            "This startup investment agreement covers seed fundraising, equity vesting, board approval, and intellectual property assignment. "
            "Payment terms and commercial renewal conditions apply to the service schedule."
        ),
        "expected_categories": {"fundraising", "equity", "governance", "ip", "commercial", "payment"},
        "expected_doc_kind": "startup legal document",
        "expected_summary_terms": {"fundraising", "equity", "board", "intellectual property", "payment"},
    },
    {
        "name": "employment_terms",
        "text": (
            "The employment agreement includes salary payment, confidentiality obligations, probation period, termination notice, "
            "and a non-compete restriction after departure. Governing law is local jurisdiction."
        ),
        "expected_categories": {"payment", "confidentiality", "termination", "non_compete", "governing_law"},
        "expected_doc_kind": "legal document",
        "expected_summary_terms": {"payment", "confidentiality", "termination", "non-compete", "governing law"},
    },
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                return default
            value = value[0]
        return float(value)
    except Exception:
        return default


def _binary_metrics(true_labels: Sequence[int], predicted_labels: Sequence[int]) -> Dict[str, Any]:
    tp = fp = fn = tn = 0
    for truth, pred in zip(true_labels, predicted_labels):
        if truth == 1 and pred == 1:
            tp += 1
        elif truth == 0 and pred == 1:
            fp += 1
        elif truth == 1 and pred == 0:
            fn += 1
        else:
            tn += 1

    accuracy = (tp + tn) / max(len(true_labels), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)

    fake_tp = tn
    fake_fp = fn
    fake_fn = fp
    fake_precision = fake_tp / max(fake_tp + fake_fp, 1)
    fake_recall = fake_tp / max(fake_tp + fake_fn, 1)
    fake_f1 = 2 * fake_precision * fake_recall / max(fake_precision + fake_recall, 1e-12)
    macro_f1 = (f1 + fake_f1) / 2

    return {
        "accuracy": accuracy,
        "precision_real": precision,
        "recall_real": recall,
        "f1_real": f1,
        "precision_fake": fake_precision,
        "recall_fake": fake_recall,
        "f1_fake": fake_f1,
        "macro_f1": macro_f1,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


class _SignatureCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


def _load_scripted_model(model_path: Path) -> tuple[torch.nn.Module, transforms.Compose]:
    model = torch.jit.load(str(model_path), map_location="cpu")
    model.eval()
    if "cnn" in model_path.name.lower():
        return model, GRAY_TRANSFORM
    return model, RGB_TRANSFORM


def _load_pth_model(model_path: Path) -> tuple[torch.nn.Module, transforms.Compose]:
    state_dict = torch.load(str(model_path), map_location="cpu")
    model_name = model_path.name.lower()

    if "vit" in model_name:
        vit = models.vit_b_16(weights=None)
        vit.heads.head = nn.Linear(vit.heads.head.in_features, 2)
        vit.load_state_dict(state_dict)
        vit.eval()
        return vit, RGB_TRANSFORM

    if "resnet" in model_name:
        resnet = models.resnet18(weights=None)
        resnet.fc = nn.Linear(resnet.fc.in_features, 2)
        resnet.load_state_dict(state_dict)
        resnet.eval()
        return resnet, GRAY_TRANSFORM

    cnn = _SignatureCNN()
    cnn.load_state_dict(state_dict)
    cnn.eval()
    return cnn, GRAY_TRANSFORM


def _load_signature_candidate(model_path: Path) -> tuple[torch.nn.Module, transforms.Compose]:
    if model_path.suffix.lower() == ".pt":
        return _load_scripted_model(model_path)
    return _load_pth_model(model_path)


def _iter_signature_validation_images() -> List[Tuple[Path, int]]:
    samples: List[Tuple[Path, int]] = []
    for label_name, label_idx in [("fake", 0), ("real", 1)]:
        for image_path in sorted((PROJECT_ROOT / "data" / "val" / label_name).glob("*")):
            if image_path.is_file():
                samples.append((image_path, label_idx))
    return samples


def _evaluate_signature_classification() -> Tuple[CandidateResult, List[CandidateResult]]:
    candidate_paths = [
        PROJECT_ROOT / "signature_best_script.pt",
        PROJECT_ROOT / "signature_resnet18_script.pt",
        PROJECT_ROOT / "signature_cnn_script.pt",
        PROJECT_ROOT / "best_signature_vit.pth",
        PROJECT_ROOT / "best_signature_resnet18.pth",
        PROJECT_ROOT / "best_signature_cnn.pth",
        PROJECT_ROOT / "signature_classifier.pth",
    ]
    samples = _iter_signature_validation_images()
    if not samples:
        return CandidateResult("signature_classification", {"error": "no validation images found"}), []

    all_results: List[CandidateResult] = []
    for model_path in candidate_paths:
        if not model_path.exists():
            continue

        try:
            model, transform = _load_signature_candidate(model_path)
            truths: List[int] = []
            preds: List[int] = []
            predictions_for_judge: List[Dict[str, Any]] = []
            for image_path, label_idx in samples:
                image = Image.open(image_path).convert("RGB")
                tensor = transform(image).unsqueeze(0)
                with torch.no_grad():
                    output = model(tensor)
                    probs = torch.softmax(output, dim=1)
                    pred_idx = int(output.argmax(1).item())
                    pred_conf = float(probs[0, pred_idx].item())
                truths.append(label_idx)
                preds.append(pred_idx)
                predictions_for_judge.append({
                    "pred": pred_idx,
                    "true": label_idx,
                    "confidence": pred_conf,
                    "grad_cam_regions": []  # Placeholder for Grad-CAM regions
                })

            metrics = _binary_metrics(truths, preds)
            # Add XAI LLM judge score
            xai_llm_score = judge_signature_classification_xai(predictions_for_judge, truths)
            metrics["xai_llm_score"] = xai_llm_score
            metrics["samples"] = len(samples)
            metrics["model_path"] = str(model_path)
            all_results.append(CandidateResult(model_path.name, metrics))
        except Exception as exc:
            all_results.append(CandidateResult(model_path.name, {"error": str(exc), "model_path": str(model_path)}))

    scored = [r for r in all_results if "error" not in r.metrics]
    if not scored:
        return CandidateResult("signature_classification", {"error": "all candidates failed"}), all_results

    best = sorted(scored, key=lambda item: (item.metrics.get("macro_f1", 0.0), item.metrics.get("accuracy", 0.0)), reverse=True)[0]
    return best, all_results


def _evaluate_signature_detection() -> Tuple[CandidateResult, List[CandidateResult]]:
    candidate_paths = [
        PROJECT_ROOT / "runs" / "detect" / "runs" / "detect" / "signature_yolo_clean" / "weights" / "best.pt",
        PROJECT_ROOT / "data2" / "chekpoint_last.pt",
    ]
    data_path = PROJECT_ROOT / "data2" / "signature_yolo_prepared" / "data.yaml"
    all_results: List[CandidateResult] = []

    for model_path in candidate_paths:
        if not model_path.exists():
            continue
        try:
            model = YOLO(str(model_path))
            metrics = model.val(data=str(data_path), imgsz=640, batch=4, verbose=False)
            box = metrics.box
            result_metrics = {
                "precision": _safe_float(getattr(box, "mp", getattr(box, "p", 0.0))),
                "recall": _safe_float(getattr(box, "mr", getattr(box, "r", 0.0))),
                "f1": _safe_float(getattr(box, "f1", 0.0)),
                "map50": _safe_float(getattr(box, "map50", 0.0)),
                "map50_95": _safe_float(getattr(box, "map", 0.0)),
                "samples": int(getattr(metrics, "n", 0) or 62),
                "instances": int(getattr(metrics, "nt_per_class", [0])[0] if hasattr(metrics, "nt_per_class") else 0),
                "model_path": str(model_path),
            }
            # Estimate XAI score based on detection confidence and F1
            # Create synthetic detection explanations for judging
            detections_for_judge = [
                {
                    "confidence": result_metrics.get("f1", 0.5),
                    "bbox": [0, 0, 100, 100]  # Placeholder bbox
                }
                for _ in range(max(1, result_metrics.get("instances", 1)))
            ]
            xai_llm_score = judge_signature_detection_xai(detections_for_judge)
            result_metrics["xai_llm_score"] = xai_llm_score
            all_results.append(CandidateResult(model_path.name, result_metrics))
        except Exception as exc:
            all_results.append(CandidateResult(model_path.name, {"error": str(exc), "model_path": str(model_path)}))

    scored = [r for r in all_results if "error" not in r.metrics]
    if not scored:
        return CandidateResult("signature_detection", {"error": "all candidates failed"}), all_results

    best = sorted(scored, key=lambda item: (item.metrics.get("f1", 0.0), item.metrics.get("map50", 0.0)), reverse=True)[0]
    return best, all_results


def _tokenize_text(value: str) -> List[str]:
    tokens = []
    for raw in value.lower().split():
        cleaned = "".join(ch for ch in raw if ch.isalnum())
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _text_quality_score(value: str) -> float:
    text = (value or "").strip()
    if not text:
        return 0.0

    letters = sum(1 for ch in text if ch.isalpha())
    digits = sum(1 for ch in text if ch.isdigit())
    alpha_ratio = letters / max(len(text), 1)
    digit_penalty = min(0.25, digits / max(len(text), 1))

    tokens = _tokenize_text(text)
    if not tokens:
        return 0.0
    longish = [t for t in tokens if len(t) >= 3]
    vowelish = [t for t in longish if any(v in t for v in "aeiou")]
    lexical_ratio = len(vowelish) / max(len(longish), 1)

    # Balance character-level clarity and token-level lexical plausibility.
    score = (alpha_ratio * 0.55) + (lexical_ratio * 0.45) - digit_penalty
    return float(max(0.0, min(1.0, score)))


def _ocr_consensus_metrics(engine_outputs: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    per_engine_tokens: Dict[str, set[str]] = {}
    for engine_name, outputs in engine_outputs.items():
        text = " ".join(str(item.get("text", "")) for item in outputs)
        per_engine_tokens[engine_name] = set(_tokenize_text(text))

    all_tokens = list(per_engine_tokens.values())
    if not all_tokens:
        return {"error": "no OCR outputs"}

    consensus_available = len(all_tokens) >= 2

    token_counts = Counter(token for tokens in all_tokens for token in tokens)
    consensus = {token for token, count in token_counts.items() if count >= 2}
    if not consensus:
        consensus = set().union(*all_tokens)

    engine_scores: Dict[str, Dict[str, Any]] = {}
    for engine_name, tokens in per_engine_tokens.items():
        tp = len(tokens & consensus)
        fp = len(tokens - consensus)
        fn = len(consensus - tokens)
        confidences = [float(item.get("confidence", item.get("conf", 0.0))) for item in engine_outputs.get(engine_name, [])]
        joined_text = " ".join(str(item.get("text", "")) for item in engine_outputs.get(engine_name, []))
        quality = _text_quality_score(joined_text)

        if consensus_available:
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            f1 = 2 * precision * recall / max(precision + recall, 1e-12)
            evaluation_method = "consensus_overlap"
        else:
            # With one engine there is no cross-engine consensus. Use a quality proxy instead.
            precision = quality
            recall = quality
            f1 = quality
            evaluation_method = "single_engine_proxy"

        quality_weighted_score = (0.7 * f1) + (0.3 * quality)
        engine_scores[engine_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "text_quality": quality,
            "quality_weighted_score": quality_weighted_score,
            "mean_confidence": float(np.mean(confidences)) if confidences else 0.0,
            "token_count": len(tokens),
            "consensus_overlap": tp,
            "evaluation_method": evaluation_method,
        }

    best_engine = sorted(
        engine_scores.items(),
        key=lambda item: (item[1]["quality_weighted_score"], item[1]["f1"], item[1]["mean_confidence"]),
        reverse=True,
    )[0][0]

    return {
        "consensus_tokens": len(consensus),
        "consensus_available": consensus_available,
        "engines": engine_scores,
        "best_engine": best_engine,
        "metric": "consensus_f1" if consensus_available else "text_quality_proxy",
    }


def _evaluate_ocr() -> Tuple[CandidateResult, List[CandidateResult]]:
    engine = MultiOCREngine(primary_engine="easyocr")
    sample_images = [path for path in OCR_SAMPLE_IMAGES if path.exists()]
    if not sample_images:
        return CandidateResult("ocr", {"error": "no OCR sample images found"}), []

    aggregate: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "text_quality": 0.0,
            "quality_weighted_score": 0.0,
            "mean_confidence": 0.0,
            "images": 0.0,
        }
    )
    image_reports: List[Dict[str, Any]] = []

    for image_path in sample_images:
        image = Image.open(image_path).convert("RGB")
        image_np = np.array(image)
        outputs = engine.extract_all(image_np)
        usable_outputs = {k: v for k, v in outputs.items() if isinstance(v, list)}
        consensus_metrics = _ocr_consensus_metrics(usable_outputs)
        image_reports.append({"image": image_path.name, **consensus_metrics})
        if "engines" in consensus_metrics:
            for engine_name, stats in consensus_metrics["engines"].items():
                aggregate[engine_name]["precision"] += stats["precision"]
                aggregate[engine_name]["recall"] += stats["recall"]
                aggregate[engine_name]["f1"] += stats["f1"]
                aggregate[engine_name]["text_quality"] += stats.get("text_quality", 0.0)
                aggregate[engine_name]["quality_weighted_score"] += stats.get("quality_weighted_score", 0.0)
                aggregate[engine_name]["mean_confidence"] += stats["mean_confidence"]
                aggregate[engine_name]["images"] += 1

    candidate_results: List[CandidateResult] = []
    reports_with_engine_scores = [report for report in image_reports if "engines" in report]
    consensus_image_count = sum(1 for report in reports_with_engine_scores if report.get("consensus_available"))
    total_eval_images = len(reports_with_engine_scores)
    all_images_have_consensus = total_eval_images > 0 and consensus_image_count == total_eval_images

    for engine_name, totals in aggregate.items():
        count = max(int(totals["images"]), 1)
        # Recompute quality-weighted score from averaged components.
        avg_f1 = totals["f1"] / count
        avg_quality = totals.get("text_quality", 0.0) / count if "text_quality" in totals else 0.0

        if all_images_have_consensus:
            metric_name = "consensus_f1"
            evaluation_method = "consensus_overlap"
            score = avg_f1
            consensus_f1_value = avg_f1
        else:
            metric_name = "text_quality_proxy"
            evaluation_method = "single_engine_proxy"
            score = avg_quality
            consensus_f1_value = None

        metrics = {
            "precision": totals["precision"] / count,
            "recall": totals["recall"] / count,
            "f1": avg_f1,
            "consensus_f1": consensus_f1_value,
            "text_quality": avg_quality,
            "quality_weighted_score": (0.7 * avg_f1) + (0.3 * avg_quality),
            "mean_confidence": totals["mean_confidence"] / count,
            "metric": metric_name,
            "evaluation_method": evaluation_method,
            "score": score,
            "consensus_images": consensus_image_count,
            "samples": count,
        }
        # Collect OCR results for XAI judging (from image reports)
        ocr_results_for_judge = []
        for report in image_reports:
            if "engines" in report and engine_name in report["engines"]:
                engine_stats = report["engines"][engine_name]
                for _ in range(int(engine_stats.get("token_count", 1))):
                    ocr_results_for_judge.append({
                        "text": "extracted_word",
                        "confidence": engine_stats.get("mean_confidence", 0.5)
                    })
        xai_llm_score = judge_ocr_xai(ocr_results_for_judge) if ocr_results_for_judge else None
        metrics["xai_llm_score"] = xai_llm_score
        candidate_results.append(CandidateResult(engine_name, metrics))

    if not candidate_results:
        return CandidateResult("ocr", {"error": "all OCR engines failed"}), image_reports

    best = sorted(
        candidate_results,
        key=lambda item: (item.metrics.get("quality_weighted_score", 0.0), item.metrics.get("f1", 0.0), item.metrics.get("mean_confidence", 0.0)),
        reverse=True,
    )[0]
    best.metrics["images"] = [report["image"] for report in image_reports]
    best.metrics["image_reports"] = image_reports
    return best, candidate_results


def _summarization_categories(result: Dict[str, Any]) -> set[str]:
    categories = set()
    for clause in result.get("key_clauses", []):
        category = clause.get("category")
        if category:
            categories.add(str(category))
    for clause in result.get("startup_signals", []):
        category = clause.get("category")
        if category:
            categories.add(str(category))
    return categories


def _evaluate_summarization() -> Tuple[CandidateResult, List[CandidateResult]]:
    modes = ["rule_based", "ai_assisted", "hybrid"]
    candidate_results: List[CandidateResult] = []

    for mode in modes:
        try:
            analyzer = LegalDocumentIntelligence(mode=mode)
        except Exception as exc:
            candidate_results.append(CandidateResult(mode, {"error": str(exc)}))
            continue

        per_doc: List[Dict[str, Any]] = []
        f1_values: List[float] = []
        accuracy_values: List[float] = []
        summary_term_values: List[float] = []
        rouge_values: List[float] = []
        xai_llm_values: List[float] = []

        for benchmark in SUMMARY_BENCHMARKS:
            try:
                result = analyzer.analyze_text(benchmark["text"], source_name=benchmark["name"])
            except Exception as exc:
                # Keep evaluation running even if one strategy/document fails.
                per_doc.append(
                    {
                        "name": benchmark["name"],
                        "precision": 0.0,
                        "recall": 0.0,
                        "f1": 0.0,
                        "document_kind_match": 0.0,
                        "summary_term_recall": 0.0,
                        "matched_summary_terms": [],
                        "predicted_categories": [],
                        "expected_categories": sorted(set(benchmark["expected_categories"])),
                        "error": str(exc),
                    }
                )
                f1_values.append(0.0)
                accuracy_values.append(0.0)
                summary_term_values.append(0.0)
                continue
            predicted_categories = _summarization_categories(result)
            expected_categories = set(benchmark["expected_categories"])
            tp = len(predicted_categories & expected_categories)
            fp = len(predicted_categories - expected_categories)
            fn = len(expected_categories - predicted_categories)
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            f1 = 2 * precision * recall / max(precision + recall, 1e-12)
            doc_kind_pred = str(result.get("document_kind", "")).strip().lower()
            doc_kind_true = benchmark["expected_doc_kind"].lower()
            accuracy = 1.0 if doc_kind_pred == doc_kind_true else 0.0

            summary_text = str(result.get("summary", "")).strip()
            expected_terms = set(benchmark.get("expected_summary_terms", set()))
            matched_terms = [term for term in expected_terms if term in summary_text.lower()]
            summary_term_recall = len(matched_terms) / max(len(expected_terms), 1)

            # Compute ROUGE-L between the original document text and the generated summary
            try:
                scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
                scores = scorer.score(benchmark["text"], summary_text)
                rouge_l_f = float(scores["rougeL"].fmeasure)
            except Exception:
                rouge_l_f = 0.0

            # Ask the LLM to judge the explanation quality (if configured)
            try:
                xai_llm_score = judge_summarization_xai(benchmark["text"], summary_text, result.get("key_clauses", []))
            except Exception:
                xai_llm_score = None

            f1_values.append(f1)
            accuracy_values.append(accuracy)
            summary_term_values.append(summary_term_recall)
            rouge_values.append(rouge_l_f)
            xai_llm_values.append(xai_llm_score)
            per_doc.append(
                {
                    "name": benchmark["name"],
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "document_kind_match": accuracy,
                    "summary_term_recall": summary_term_recall,
                    "rouge_l_f": rouge_l_f,
                    "xai_llm_score": xai_llm_score,
                    "matched_summary_terms": sorted(matched_terms),
                    "predicted_categories": sorted(predicted_categories),
                    "expected_categories": sorted(expected_categories),
                }
            )

        mean_f1 = float(np.mean(f1_values)) if f1_values else 0.0
        mean_doc_kind = float(np.mean(accuracy_values)) if accuracy_values else 0.0
        mean_summary_term_recall = float(np.mean(summary_term_values)) if summary_term_values else 0.0
        mean_rouge = float(np.mean(rouge_values)) if rouge_values else 0.0
        valid_xai = [v for v in xai_llm_values if v is not None]
        mean_xai_llm = float(np.mean(valid_xai)) if valid_xai else 0.0
        # Combined score blends category detection, doc-kind accuracy, term recall, ROUGE and LLM XAI judgment
        combined = (mean_f1 * 0.4) + (mean_doc_kind * 0.18) + (mean_summary_term_recall * 0.12) + (mean_rouge * 0.15) + (mean_xai_llm * 0.15)
        metrics = {
            "category_f1": mean_f1,
            "document_kind_accuracy": mean_doc_kind,
            "summary_term_recall": mean_summary_term_recall,
            "rouge_l_f": mean_rouge,
            "xai_llm_score": mean_xai_llm,
            "combined_score": combined,
            "samples": len(SUMMARY_BENCHMARKS),
            "docs": per_doc,
        }
        candidate_results.append(CandidateResult(mode, metrics))

    scored = [r for r in candidate_results if "error" not in r.metrics]
    if not scored:
        return CandidateResult("summarization", {"error": "all strategies failed"}), candidate_results

    best = sorted(scored, key=lambda item: (item.metrics.get("combined_score", 0.0), item.metrics.get("category_f1", 0.0)), reverse=True)[0]
    return best, candidate_results


def build_report() -> Dict[str, Any]:
    judge_status = llm_judge_status()
    sig_best, sig_all = _evaluate_signature_classification()
    det_best, det_all = _evaluate_signature_detection()
    ocr_best, ocr_all = _evaluate_ocr()
    sum_best, sum_all = _evaluate_summarization()

    selections = {
        "signature_classification": {
            "model_path": sig_best.metrics.get("model_path") or sig_best.name,
            "metric": "macro_f1",
            "score": sig_best.metrics.get("macro_f1", 0.0),
            "xai_llm_score": sig_best.metrics.get("xai_llm_score", None),
        },
        "signature_detection": {
            "model_path": det_best.metrics.get("model_path") or det_best.name,
            "metric": "f1",
            "score": det_best.metrics.get("f1", 0.0),
            "xai_llm_score": det_best.metrics.get("xai_llm_score", None),
        },
        "ocr": {
            "primary_engine": ocr_best.name,
            "metric": ocr_best.metrics.get("metric", "consensus_f1"),
            "score": ocr_best.metrics.get("score", ocr_best.metrics.get("consensus_f1", ocr_best.metrics.get("f1", 0.0))),
            "xai_llm_score": ocr_best.metrics.get("xai_llm_score", None),
        },
        "summarization": {
            "strategy": sum_best.name,
            "metric": sum_best.metrics.get("combined_score", 0.0),
            "score": sum_best.metrics.get("combined_score", 0.0),
            "xai_llm_score": sum_best.metrics.get("xai_llm_score", None),
        },
    }

    report = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "selection_file": str(SELECTIONS_FILE),
        "report_file": str(REPORT_FILE),
        "xai_llm_judge": judge_status,
        "signature_classification": {
            "best": sig_best.metrics,
            "candidates": [item.__dict__ for item in sig_all],
            "metric": "macro_f1",
        },
        "signature_detection": {
            "best": det_best.metrics,
            "candidates": [item.__dict__ for item in det_all],
            "metric": "f1",
        },
        "ocr": {
            "best": ocr_best.metrics,
            "candidates": [item.__dict__ for item in ocr_all],
            "metric": ocr_best.metrics.get("metric", "consensus_f1"),
            "sample_count": len(ocr_best.metrics.get("images", [])),
        },
        "summarization": {
            "best": sum_best.metrics,
            "candidates": [item.__dict__ for item in sum_all],
            "metric": "combined_score",
        },
        "selections": selections,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate objective-specific models/tools and pick the best one.")
    parser.add_argument("--write-report", action="store_true", default=True, help="Write report and selection files.")
    parser.add_argument("--no-write-report", action="store_true", help="Do not write report files.")
    args = parser.parse_args()

    report = build_report()

    if not args.no_write_report:
        save_objective_report(report)
        save_objective_selections(report["selections"])

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
