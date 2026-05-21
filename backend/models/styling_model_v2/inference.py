"""Inference helpers for the styling_model_v2 recommendation bundle.

The bundle combines a trained multi-output scikit-learn model with input and
target label encoders. It returns wardrobe guidance that can be used for pitch
day outfit selection.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping
import json

import joblib
import numpy as np


MODEL_DIR = Path(__file__).resolve().parent
METADATA_PATH = MODEL_DIR / "metadata_v2.json"
MODEL_PATH = MODEL_DIR / "styling_model_v2.pkl"
INPUT_ENCODERS_PATH = MODEL_DIR / "input_encoders.pkl"
TARGET_ENCODERS_PATH = MODEL_DIR / "target_encoders.pkl"
COLOR_SEMANTICS_PATH = MODEL_DIR / "color_semantics.pkl"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_styling_bundle() -> dict[str, Any]:
    """Load the model and its metadata once per process."""
    metadata = _load_json(METADATA_PATH)

    return {
        "metadata": metadata,
        "model": joblib.load(MODEL_PATH),
        "input_encoders": joblib.load(INPUT_ENCODERS_PATH),
        "target_encoders": joblib.load(TARGET_ENCODERS_PATH),
        "color_semantics": joblib.load(COLOR_SEMANTICS_PATH),
        "input_cols": list(metadata.get("input_cols", [])),
        "target_cols": list(metadata.get("target_cols", [])),
    }


def _format_category(value: Any, encoder) -> str:
    classes = [str(item) for item in getattr(encoder, "classes_", [])]
    if not classes:
        raise ValueError("Input encoder is missing classes.")

    if value is None:
        return classes[0]

    candidate = str(value).strip()
    if not candidate:
        return classes[0]

    if candidate in classes:
        return candidate

    lowered_lookup = {item.lower(): item for item in classes}
    lowered = candidate.lower()
    if lowered in lowered_lookup:
        return lowered_lookup[lowered]

    normalized = " ".join(part.capitalize() for part in lowered.replace("_", " ").split())
    if normalized in classes:
        return normalized

    return classes[0]


def _as_int(value: Any) -> Any:
    try:
        return int(value)
    except Exception:
        return value


def _resolve_probability(classes: list[Any], probability_row: np.ndarray, predicted_value: Any) -> float:
    if probability_row is None or len(probability_row) == 0:
        return 0.0

    predicted_value = _as_int(predicted_value)
    class_values = [_as_int(item) for item in classes]
    if predicted_value in class_values:
        index = class_values.index(predicted_value)
        return float(probability_row[index])

    return float(np.max(probability_row))


def _extract_color_families(recommended_colors: str, semantics: Mapping[str, Any]) -> list[str]:
    palette_map = semantics.get("PALETTE_TO_FAMILIES", {})
    families: set[str] = set()

    for token in (piece.strip().lower() for piece in recommended_colors.split(",")):
        if not token:
            continue
        for family in palette_map.get(token, []):
            families.add(str(family))

    return sorted(families)


def _build_pitch_day_summary(profile: Mapping[str, Any], predictions: Mapping[str, str], families: list[str]) -> str:
    colors = predictions.get("Recommended Clothing Colors", "neutral tones")
    avoid = predictions.get("Avoid Clothing Colors", "anything overly loud")
    fit = predictions.get("Recommended Fitting Style", "Balanced Fit")
    materials = predictions.get("Recommended Materials", "Structured Cotton")

    family_text = f" These colors align with {'/'.join(families)}." if families else ""
    context = []
    for key in ["Hair Color", "Eye Color", "Skin Tone", "Under Tone", "Torso length", "Body Proportion"]:
        if profile.get(key):
            context.append(f"{key.lower()}: {profile[key]}")

    context_text = f" Profile used: {', '.join(context)}." if context else ""

    return (
        f"For pitch day, choose a {fit.lower()} outfit in {materials.lower()} and lean into {colors.lower()}."
        f" Avoid {avoid.lower()} to keep the look clean on stage and on camera.{family_text}{context_text}"
    )


def prepare_styling_input(profile: Mapping[str, Any]) -> dict[str, Any]:
    bundle = load_styling_bundle()
    encoded_row: list[int] = []
    normalized_profile: dict[str, str] = {}

    for column in bundle["input_cols"]:
        encoder = bundle["input_encoders"][column]
        normalized_value = _format_category(profile.get(column), encoder)
        normalized_profile[column] = normalized_value
        encoded_row.append(int(encoder.transform([normalized_value])[0]))

    return {
        "encoded_features": np.asarray([encoded_row], dtype=float),
        "normalized_profile": normalized_profile,
    }


def predict_styling_recommendation(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Return pitch-day styling recommendations for the provided profile."""
    bundle = load_styling_bundle()
    prepared = prepare_styling_input(profile)
    model = bundle["model"]
    encoded_predictions = model.predict(prepared["encoded_features"])[0]
    probability_outputs = model.predict_proba(prepared["encoded_features"])

    decoded_predictions: dict[str, str] = {}
    confidence_by_target: dict[str, float] = {}

    for index, target_name in enumerate(bundle["target_cols"]):
        target_encoder = bundle["target_encoders"][target_name]
        encoded_value = _as_int(encoded_predictions[index])
        decoded_value = target_encoder.inverse_transform([encoded_value])[0]
        decoded_predictions[target_name] = str(decoded_value)

        estimator_classes = list(getattr(model.estimators_[index], "classes_", []))
        probability_row = probability_outputs[index][0] if index < len(probability_outputs) else np.array([])
        confidence_by_target[target_name] = round(
            _resolve_probability(estimator_classes, probability_row, encoded_value),
            4,
        )

    recommended_families = _extract_color_families(
        decoded_predictions.get("Recommended Clothing Colors", ""),
        bundle["color_semantics"],
    )

    overall_confidence = round(
        float(np.mean(list(confidence_by_target.values()))) if confidence_by_target else 0.0,
        4,
    )

    return {
        "available": True,
        "model": "styling_model_v2",
        "version": bundle["metadata"].get("version", 2),
        "input_profile": prepared["normalized_profile"],
        "predictions": decoded_predictions,
        "confidence": confidence_by_target,
        "overall_confidence": overall_confidence,
        "recommended_color_families": recommended_families,
        "pitch_day_summary": _build_pitch_day_summary(
            prepared["normalized_profile"],
            decoded_predictions,
            recommended_families,
        ),
    }


__all__ = [
    "load_styling_bundle",
    "prepare_styling_input",
    "predict_styling_recommendation",
]