import os
import re
import json
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[2]
SRS_DIR = BACKEND_DIR / "SRS"
SRS_DATA_DIR = SRS_DIR / "srs_data"
SRS_GENERATION_DIR = SRS_DATA_DIR / "generation"
SRS_OUTPUTS_DIR = SRS_DIR / "srs_outputs"

SRS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_read_csv(path):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, encoding="latin-1")
        except Exception:
            return pd.DataFrame()


def safe_read_text(path):
    path = Path(path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""


def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text):
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "srs_project"


def get_project_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_available_data_summary():
    files = {
        "c6_fr_nfr": SRS_DATA_DIR / "c6_deep_fr_nfr_predictions.csv",
        "c7_nfr_subtypes": SRS_DATA_DIR / "c7_nfr_subtype_predictions.csv",
        "c8_ambiguity": SRS_DATA_DIR / "c8_deep_ambiguity_predictions.csv",
        "c8_doc_ambiguity": SRS_DATA_DIR / "c8_document_ambiguity_summary.csv",
        "c9_quality": SRS_DATA_DIR / "c9_multimodal_requirement_quality_scores.csv",
        "c10_rewrites": SRS_DATA_DIR / "c10_llm_requirement_rewrites.csv",
        "c11_requirement_report": SRS_DATA_DIR / "c11_final_requirement_report.csv",
        "c11_document_report": SRS_DATA_DIR / "c11_final_document_report.csv",
        "v7_vision": SRS_DATA_DIR / "v7_page_vision_predictions.csv",
        "generation_requirements": SRS_GENERATION_DIR / "generated_requirements_sample.csv",
        "generation_sections": SRS_GENERATION_DIR / "generated_sections_sample.csv",
        "rag_references": SRS_GENERATION_DIR / "rag_references_sample.csv",
    }

    summary = {}
    for key, path in files.items():
        df = safe_read_csv(path)
        summary[key] = {
            "exists": path.exists(),
            "path": str(path),
            "rows": int(len(df)) if not df.empty else 0,
            "columns": list(df.columns)[:20] if not df.empty else [],
        }

    return summary


def detect_column(df, candidates):
    if df.empty:
        return None

    normalized = {c.lower().strip(): c for c in df.columns}

    for candidate in candidates:
        candidate_norm = candidate.lower().strip()
        if candidate_norm in normalized:
            return normalized[candidate_norm]

    for col in df.columns:
        col_norm = col.lower().strip()
        for candidate in candidates:
            if candidate.lower().strip() in col_norm:
                return col

    return None


def create_zip_package(project_slug, files):
    zip_path = SRS_OUTPUTS_DIR / f"{project_slug}_srs_package.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            file_path = Path(file_path)
            if file_path.exists():
                zipf.write(file_path, arcname=file_path.name)

    return str(zip_path)