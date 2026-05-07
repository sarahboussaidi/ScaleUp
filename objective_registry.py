"""Shared selection registry for objective-specific best models and tools."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
GENERATED_DIR = PROJECT_ROOT / "generated"
SELECTIONS_FILE = GENERATED_DIR / "objective_selections.json"
REPORT_FILE = GENERATED_DIR / "objective_evaluation_report.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_objective_selections() -> Dict[str, Any]:
    return _read_json(SELECTIONS_FILE)


def save_objective_selections(data: Dict[str, Any]) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    SELECTIONS_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return SELECTIONS_FILE


def load_objective_report() -> Dict[str, Any]:
    return _read_json(REPORT_FILE)


def save_objective_report(data: Dict[str, Any]) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return REPORT_FILE


def get_selected_value(objective: str, key: str, default: Optional[Any] = None) -> Any:
    selections = load_objective_selections()
    return selections.get(objective, {}).get(key, default)


def get_selected_model_path(objective: str, default_candidates: list[Path]) -> Optional[Path]:
    selected = get_selected_value(objective, "model_path")
    if selected:
        selected_path = Path(str(selected))
        if not selected_path.is_absolute():
            selected_path = (PROJECT_ROOT / selected_path).resolve()
        if selected_path.exists():
            return selected_path

    for candidate in default_candidates:
        if candidate.exists():
            return candidate.resolve()
    return None
