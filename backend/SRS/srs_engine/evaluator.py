import re
from pathlib import Path

import pandas as pd

from .document_parser import split_candidate_requirements, detect_srs_sections

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .utils import (
    SRS_DATA_DIR,
    clean_text,
    safe_read_csv,
    detect_column,
    get_available_data_summary,
)


VAGUE_TERMS = [
    "fast",
    "quickly",
    "easy",
    "user-friendly",
    "efficient",
    "robust",
    "secure",
    "high performance",
    "as soon as possible",
    "many",
    "several",
    "appropriate",
    "sufficient",
    "etc",
]

EXPECTED_SECTIONS = [
    "Introduction",
    "General Description",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Interface Requirements",
    "Performance Requirements",
    "Security Requirements",
    "Acceptance Criteria",
    "Risks and Assumptions",
    "Conclusion",
]

def detect_vague_terms_with_context(text, terms=None, max_contexts=40):
    """
    Return concrete vague terms and short sentence contexts detected in the SRS.
    This is used by the frontend "See details" button and by the exported report.
    """
    if terms is None:
        terms = VAGUE_TERMS

    if not text:
        return [], []

    text_str = str(text)
    text_lower = text_str.lower()

    detected_terms = []
    for term in terms:
        count = text_lower.count(term.lower())
        if count > 0:
            detected_terms.append({
                "term": term,
                "count": int(count),
            })

    detected_terms = sorted(
        detected_terms,
        key=lambda item: (-item["count"], item["term"]),
    )

    # Split into readable sentence/line contexts.
    raw_segments = re.split(r"(?<=[.!?])\s+|[\n\r]+", text_str)
    contexts = []
    seen = set()

    for segment in raw_segments:
        clean_segment = re.sub(r"\s+", " ", segment).strip()
        if len(clean_segment) < 15:
            continue

        lower_segment = clean_segment.lower()
        for item in detected_terms:
            term = item["term"]
            if term.lower() in lower_segment:
                key = (term.lower(), clean_segment.lower())
                if key in seen:
                    continue

                seen.add(key)
                contexts.append({
                    "term": term,
                    "sentence": clean_segment[:350],
                })
                break

        if len(contexts) >= max_contexts:
            break

    return detected_terms, contexts



def compute_text_quality_scores(text):
    text = clean_text(text)
    requirements = split_candidate_requirements(text)
    found_sections = detect_srs_sections(text)

    total_expected = len(EXPECTED_SECTIONS)
    section_coverage = len(set(found_sections)) / total_expected if total_expected else 0

    detected_vague_terms, vague_term_contexts = detect_vague_terms_with_context(text, VAGUE_TERMS)
    vague_count = sum(item["count"] for item in detected_vague_terms)
    clarity_score = max(40, 100 - vague_count * 4)

    numeric_count = len(re.findall(r"\d+|%|seconds|minutes|ms|hours|days", text.lower()))
    testability_score = min(100, 55 + numeric_count * 5)

    req_count = len(requirements)
    completeness_score = min(100, section_coverage * 70 + min(req_count, 30))

    duplicate_ratio = 0
    if requirements:
        unique_reqs = len(set([r.lower() for r in requirements]))
        duplicate_ratio = 1 - (unique_reqs / len(requirements))

    consistency_score = max(50, 100 - duplicate_ratio * 100)

    feasibility_score = 80
    if "real-time" in text.lower():
        feasibility_score -= 5
    if "ai" in text.lower() or "machine learning" in text.lower():
        feasibility_score -= 5

    overall_score = round(
        (
            completeness_score * 0.25
            + clarity_score * 0.20
            + consistency_score * 0.20
            + testability_score * 0.20
            + feasibility_score * 0.15
        ),
        2,
    )

    recommendations = []

    if completeness_score < 75:
        recommendations.append("Add missing standard SRS sections such as acceptance criteria, risks, assumptions, and interface requirements.")

    if clarity_score < 80:
        recommendations.append("Replace vague words with measurable and precise constraints.")

    if testability_score < 75:
        recommendations.append("Add numeric thresholds, acceptance criteria, and measurable test conditions.")

    if consistency_score < 80:
        recommendations.append("Remove duplicated or conflicting requirements.")

    if not recommendations:
        recommendations.append("The SRS is globally strong. Minor improvements can be added for traceability and stakeholder validation.")

    return {
        "overall_score": overall_score,
        "completeness_score": round(completeness_score, 2),
        "clarity_score": round(clarity_score, 2),
        "consistency_score": round(consistency_score, 2),
        "testability_score": round(testability_score, 2),
        "feasibility_score": round(feasibility_score, 2),
        "detected_sections": found_sections,
        "missing_sections": [s for s in EXPECTED_SECTIONS if s not in found_sections],
        "requirements_count": req_count,
        "vague_terms_count": vague_count,
        "recommendations": recommendations,
    }


def summarize_notebook_outputs():
    c6 = safe_read_csv(SRS_DATA_DIR / "c6_deep_fr_nfr_predictions.csv")
    c7 = safe_read_csv(SRS_DATA_DIR / "c7_nfr_subtype_predictions.csv")
    c8 = safe_read_csv(SRS_DATA_DIR / "c8_deep_ambiguity_predictions.csv")
    c9 = safe_read_csv(SRS_DATA_DIR / "c9_multimodal_requirement_quality_scores.csv")
    c11 = safe_read_csv(SRS_DATA_DIR / "c11_final_requirement_report.csv")

    summary = {}

    if not c6.empty:
        pred_col = detect_column(c6, ["final_prediction", "deep_prediction_label", "deep_prediction", "prediction"])
        if pred_col:
            summary["fr_nfr_distribution"] = c6[pred_col].astype(str).value_counts().to_dict()

    if not c7.empty:
        subtype_col = detect_column(c7, ["nfr_subtype_pred", "nfr_subtype", "subtype"])
        if subtype_col:
            summary["nfr_subtype_distribution"] = c7[subtype_col].astype(str).value_counts().head(10).to_dict()

    if not c8.empty:
        amb_col = detect_column(c8, ["final_ambiguity_label", "ambiguity_label", "prediction"])
        if amb_col:
            summary["ambiguity_distribution"] = c8[amb_col].astype(str).value_counts().to_dict()

    if not c9.empty:
        quality_col = detect_column(c9, ["requirement_quality_score", "deep_quality_numeric_score", "quality_score"])
        if quality_col:
            summary["avg_requirement_quality_score"] = round(float(pd.to_numeric(c9[quality_col], errors="coerce").mean()), 2)

    if not c11.empty:
        summary["final_requirement_report_rows"] = int(len(c11))

    return summary


def evaluate_srs(text):
    quality = compute_text_quality_scores(text)
    notebook_summary = summarize_notebook_outputs()
    data_summary = get_available_data_summary()

    return {
        "status": "success",
        "message": "SRS evaluated successfully.",
        "evaluation": quality,
        "notebook_outputs_summary": notebook_summary,
        "available_data": data_summary,
        "xai": {
            "explanation": "The score is computed from section coverage, requirement clarity, ambiguity signals, testability, consistency, and feasibility.",
            "main_quality_drivers": [
                "Detected standard SRS sections",
                "Number of requirement-like sentences",
                "Presence of vague terms",
                "Presence of measurable numeric constraints",
                "Duplicate or repeated requirements",
            ],
        },
    }



def find_text_column(df):
    if df is None or df.empty:
        return None

    candidates = [
        "requirement_text",
        "text",
        "clean_text",
        "sentence",
        "requirement",
        "generated_requirement_text",
        "rewritten_requirement",
        "original_requirement",
    ]

    for col in candidates:
        if col in df.columns:
            return col

    # fallback: longest object column
    object_cols = [c for c in df.columns if df[c].dtype == "object"]

    if not object_cols:
        return None

    return max(object_cols, key=lambda c: df[c].astype(str).str.len().mean())


def match_requirements_with_output(document_requirements, df, min_similarity=0.25, max_matches=50):
    """
    Match uploaded-document requirements with notebook output rows.
    This creates document-specific links to previous model outputs.
    """
    if df is None or df.empty or not document_requirements:
        return []

    text_col = find_text_column(df)

    if not text_col:
        return []

    corpus = [str(x) for x in document_requirements] + df[text_col].astype(str).tolist()

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=10000,
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(corpus)

        doc_vectors = matrix[:len(document_requirements)]
        output_vectors = matrix[len(document_requirements):]

        sims = cosine_similarity(doc_vectors, output_vectors)

        matches = []

        for i, req in enumerate(document_requirements):
            best_idx = int(sims[i].argmax())
            best_score = float(sims[i][best_idx])

            if best_score >= min_similarity:
                row = df.iloc[best_idx].astype(str).to_dict()
                matches.append({
                    "uploaded_requirement": req,
                    "matched_output_text": str(df.iloc[best_idx][text_col]),
                    "similarity": round(best_score, 4),
                    "matched_row": row
                })

        matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)
        return matches[:max_matches]

    except Exception as e:
        return [{
            "error": f"Matching failed: {str(e)}"
        }]


def summarize_document_specific_matches(document_requirements, outputs):
    """
    Build document-specific model evidence using matching against notebook outputs.
    """
    fr_nfr_matches = match_requirements_with_output(document_requirements, outputs.get("fr_nfr"))
    nfr_matches = match_requirements_with_output(document_requirements, outputs.get("nfr_subtype"))
    ambiguity_matches = match_requirements_with_output(document_requirements, outputs.get("ambiguity"))
    quality_matches = match_requirements_with_output(document_requirements, outputs.get("quality"))
    rewrite_matches = match_requirements_with_output(document_requirements, outputs.get("rewrites"))

    return {
        "uploaded_requirement_count": len(document_requirements),
        "matched_fr_nfr_count": len(fr_nfr_matches),
        "matched_nfr_subtype_count": len(nfr_matches),
        "matched_ambiguity_count": len(ambiguity_matches),
        "matched_quality_count": len(quality_matches),
        "matched_rewrite_count": len(rewrite_matches),

        "fr_nfr_matches": fr_nfr_matches[:10],
        "nfr_subtype_matches": nfr_matches[:10],
        "ambiguity_matches": ambiguity_matches[:10],
        "quality_matches": quality_matches[:10],
        "rewrite_matches": rewrite_matches[:10],

        "explanation": "These results are document-specific matches between the uploaded SRS requirements and the real outputs produced by previous notebooks."
    }


def load_notebook_model_outputs():
    """
    Load real notebook outputs used for model-aware SRS evaluation.
    These files come from previous notebooks: C6, C7, C8, C9, C10, C11 and V7.
    """
    return {
        "fr_nfr": safe_read_csv(SRS_DATA_DIR / "c6_deep_fr_nfr_predictions.csv"),
        "nfr_subtype": safe_read_csv(SRS_DATA_DIR / "c7_nfr_subtype_predictions.csv"),
        "ambiguity": safe_read_csv(SRS_DATA_DIR / "c8_deep_ambiguity_predictions.csv"),
        "quality": safe_read_csv(SRS_DATA_DIR / "c9_multimodal_requirement_quality_scores.csv"),
        "rewrites": safe_read_csv(SRS_DATA_DIR / "c10_llm_requirement_rewrites.csv"),
        "final_report": safe_read_csv(SRS_DATA_DIR / "c11_final_requirement_report.csv"),
        "vision": safe_read_csv(SRS_DATA_DIR / "v7_page_vision_predictions.csv"),
        "gradcam": safe_read_csv(SRS_DATA_DIR / "v6_gradcam_xai_samples.csv"),
    }


def summarize_model_outputs_detailed(outputs):
    """
    Build a detailed summary from actual notebook model outputs.
    """
    summary = {}

    c6 = outputs.get("fr_nfr")
    c7 = outputs.get("nfr_subtype")
    c8 = outputs.get("ambiguity")
    c9 = outputs.get("quality")
    c10 = outputs.get("rewrites")
    c11 = outputs.get("final_report")
    v7 = outputs.get("vision")
    v6 = outputs.get("gradcam")

    if c6 is not None and not c6.empty:
        pred_col = detect_column(c6, [
            "final_prediction",
            "deep_prediction_label",
            "deep_prediction",
            "prediction",
            "label"
        ])
        if pred_col:
            summary["fr_nfr"] = {
                "available": True,
                "rows": int(len(c6)),
                "prediction_column": pred_col,
                "distribution": c6[pred_col].astype(str).value_counts().to_dict()
            }

    if c7 is not None and not c7.empty:
        subtype_col = detect_column(c7, [
            "nfr_subtype_pred",
            "nfr_subtype",
            "subtype",
            "prediction",
            "label"
        ])
        if subtype_col:
            summary["nfr_subtypes"] = {
                "available": True,
                "rows": int(len(c7)),
                "prediction_column": subtype_col,
                "distribution": c7[subtype_col].astype(str).value_counts().head(15).to_dict()
            }

    if c8 is not None and not c8.empty:
        amb_col = detect_column(c8, [
            "final_ambiguity_label",
            "ambiguity_label",
            "prediction",
            "label"
        ])
        if amb_col:
            summary["ambiguity"] = {
                "available": True,
                "rows": int(len(c8)),
                "prediction_column": amb_col,
                "distribution": c8[amb_col].astype(str).value_counts().to_dict()
            }

    if c9 is not None and not c9.empty:
        quality_col = detect_column(c9, [
            "requirement_quality_score",
            "deep_quality_numeric_score",
            "quality_score",
            "generated_quality_score"
        ])
        label_col = detect_column(c9, [
            "quality_label",
            "deep_quality_label",
            "generated_quality_label",
            "label"
        ])

        quality_summary = {
            "available": True,
            "rows": int(len(c9)),
        }

        if quality_col:
            numeric_scores = pd.to_numeric(c9[quality_col], errors="coerce")
            quality_summary["score_column"] = quality_col
            quality_summary["average_quality_score"] = round(float(numeric_scores.mean()), 2)

        if label_col:
            quality_summary["label_column"] = label_col
            quality_summary["distribution"] = c9[label_col].astype(str).value_counts().to_dict()

        summary["quality"] = quality_summary

    if c10 is not None and not c10.empty:
        summary["rewrites"] = {
            "available": True,
            "rows": int(len(c10)),
            "description": "LLM requirement rewriting outputs are available."
        }

    if c11 is not None and not c11.empty:
        summary["final_requirement_report"] = {
            "available": True,
            "rows": int(len(c11)),
            "description": "Final requirement-level report is available."
        }

    if v7 is not None and not v7.empty:
        page_col = detect_column(v7, [
            "predicted_page_type",
            "page_type",
            "prediction",
            "label"
        ])

        vision_summary = {
            "available": True,
            "rows": int(len(v7)),
        }

        if page_col:
            vision_summary["page_type_column"] = page_col
            vision_summary["page_type_distribution"] = v7[page_col].astype(str).value_counts().to_dict()

        summary["vision"] = vision_summary

    if v6 is not None and not v6.empty:
        summary["gradcam"] = {
            "available": True,
            "rows": int(len(v6)),
            "description": "Grad-CAM XAI samples are available from CV notebook outputs."
        }

    summary["xai"] = {
        "lime": {
            "available": True,
            "description": "LIME explanations are represented through C6/C7/C8 XAI sample files when available."
        },
        "gradcam": {
            "available": bool(v6 is not None and not v6.empty),
            "description": "Grad-CAM explanations are represented through v6_gradcam_xai_samples.csv."
        },
        "explanation": "The evaluation combines rule-based SRS quality checks with trained model outputs and XAI summaries from previous notebooks."
    }

    return summary


def compute_model_aware_score(rule_eval, model_summary):
    """
    Combine rule-based score with model output evidence.
    """
    base_score = float(rule_eval.get("overall_score", 0))

    bonus = 0
    penalty = 0

    ambiguity = model_summary.get("ambiguity", {})
    ambiguity_dist = ambiguity.get("distribution", {})

    ambiguous_count = 0
    clear_count = 0

    for label, value in ambiguity_dist.items():
        label_lower = str(label).lower()
        if "ambiguous" in label_lower:
            ambiguous_count += int(value)
        if "clear" in label_lower:
            clear_count += int(value)

    if clear_count > ambiguous_count:
        bonus += 3
    elif ambiguous_count > clear_count:
        penalty += 4

    quality = model_summary.get("quality", {})
    avg_quality = quality.get("average_quality_score")

    if avg_quality is not None:
        if avg_quality >= 80:
            bonus += 4
        elif avg_quality < 60:
            penalty += 6

    if model_summary.get("fr_nfr", {}).get("available"):
        bonus += 1

    if model_summary.get("nfr_subtypes", {}).get("available"):
        bonus += 1

    if model_summary.get("vision", {}).get("available"):
        bonus += 1

    if model_summary.get("xai", {}).get("gradcam", {}).get("available"):
        bonus += 1

    final_score = max(0, min(100, round(base_score + bonus - penalty, 2)))

    if final_score >= 85:
        label = "EXCELLENT_MODEL_AWARE_SRS"
    elif final_score >= 70:
        label = "GOOD_MODEL_AWARE_SRS"
    elif final_score >= 50:
        label = "NEEDS_IMPROVEMENT_MODEL_AWARE_SRS"
    else:
        label = "WEAK_MODEL_AWARE_SRS"

    return {
        "base_rule_score": base_score,
        "model_bonus": bonus,
        "model_penalty": penalty,
        "final_model_aware_score": final_score,
        "final_model_aware_label": label
    }


def build_model_aware_recommendations(rule_eval, model_summary, document_specific):
    recommendations = []

    recommendations.extend(rule_eval.get("recommendations", []))

    ambiguity = model_summary.get("ambiguity", {})
    ambiguity_dist = ambiguity.get("distribution", {})

    for label, value in ambiguity_dist.items():
        if "ambiguous" in str(label).lower() and int(value) > 0:
            recommendations.append(
                "Review ambiguous requirements detected by the RoBERTa ambiguity model."
            )
            break

    nfr = model_summary.get("nfr_subtypes", {})
    if nfr.get("available"):
        recommendations.append(
            "Validate NFR subtype coverage, especially security, performance, usability, availability, and maintainability."
        )

    vision = model_summary.get("vision", {})
    if vision.get("available"):
        recommendations.append(
            "Use the ResNet/CV page classification outputs to verify document structure, cover page, TOC, content pages, and appendices."
        )

    if document_specific.get("uploaded_requirement_count", 0) > 0:
        recommendations.append(
            f"{document_specific.get('uploaded_requirement_count')} requirement-like statements were extracted from the uploaded document and matched against notebook model outputs."
        )

    # remove duplicates while preserving order
    unique = []
    seen = set()

    for rec in recommendations:
        key = rec.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(rec)

    return unique[:10]


def evaluate_srs_with_models(text):
    """
    Main model-aware SRS evaluator used by Flask.
    It combines:
    - OCR/text-extracted document content
    - rule-based SRS quality scoring
    - real notebook outputs from NLP/CV/LLM/XAI modules
    - document-specific matching between uploaded requirements and notebook outputs
    """
    text = clean_text(text)

    requirements = split_candidate_requirements(text)

    rule_eval = compute_text_quality_scores(text)

    outputs = load_notebook_model_outputs()

    model_summary = summarize_model_outputs_detailed(outputs)

    document_specific = summarize_document_specific_matches(requirements, outputs)

    model_score = compute_model_aware_score(rule_eval, model_summary)

    recommendations = build_model_aware_recommendations(
        rule_eval,
        model_summary,
        document_specific
    )

    report = {
        "status": "success",
        "message": "SRS evaluated successfully using OCR/text extraction, rule-based checks, notebook model outputs, and document-specific model matching.",
        "input_statistics": {
            "text_length": len(text),
            "detected_requirement_sentences": len(requirements),
        },
        "rule_based_evaluation": rule_eval,
        "model_based_evaluation": model_summary,
        "document_specific_model_evidence": document_specific,
        "model_aware_score": model_score,
        "recommendations": recommendations,
        "xai": {
            "explanation": "The final score combines rule-based SRS quality checks with real notebook outputs from DistilBERT, RoBERTa, ResNet/CV, LIME, Grad-CAM, and LLM rewriting modules.",
            "document_specific_matching": "Uploaded document requirements are matched against previous notebook outputs using TF-IDF and cosine similarity.",
            "main_quality_drivers": [
                "Standard SRS section coverage",
                "Requirement clarity and vague language",
                "Measurable and testable constraints",
                "Duplicate or repeated requirements",
                "FR/NFR classification evidence",
                "NFR subtype coverage",
                "Ambiguity detection",
                "Multimodal requirement quality score",
                "CV page classification evidence",
                "LIME and Grad-CAM XAI availability",
            ],
        },
        "available_data": get_available_data_summary(),
    }

    return report