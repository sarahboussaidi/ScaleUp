from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_PROMPT = (
    "Summarize this legal document in 2-4 concise sentences and list the key clauses "
    "that affect obligations, risk, and compliance."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build legal instruction fine-tuning JSONL from existing evaluation reports."
    )
    parser.add_argument(
        "--report-json",
        default="generated/objective_evaluation_report.json",
        help="Path to report containing summarization benchmark rows",
    )
    parser.add_argument("--train-out", default="data/legal_train.jsonl")
    parser.add_argument("--valid-out", default="data/legal_valid.jsonl")
    parser.add_argument(
        "--lexglue-csv",
        default="lexglue/unfair_tos_train.csv",
        help="Fallback CSV used when report benchmarks are unavailable",
    )
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _simple_summary(text: str, max_sentences: int = 2) -> str:
    text = " ".join(str(text).split())
    if not text:
        return ""
    parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
    if not parts:
        return text[:320]
    picked = ". ".join(parts[:max_sentences]).strip()
    if not picked.endswith("."):
        picked += "."
    return picked


def _rows_from_lexglue(csv_path: Path, max_rows: int) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []

    import csv

    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for item in reader:
            text = str(item.get("text", "")).strip()
            if len(text) < 80:
                continue
            target = _simple_summary(text, max_sentences=2)
            if not target:
                continue
            rows.append(
                {
                    "prompt": DEFAULT_PROMPT + "\n\nDocument:\n" + text,
                    "target": target,
                }
            )
            if len(rows) >= max_rows:
                break
    return rows


def _extract_rows(report: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    benchmarks = (
        report.get("objectives", {})
        .get("summarization", {})
        .get("benchmarks", [])
    )

    for item in benchmarks:
        source_text = str(item.get("source", "")).strip()
        reference = str(item.get("reference", "")).strip()
        if not source_text or not reference:
            continue
        rows.append(
            {
                "prompt": DEFAULT_PROMPT + "\n\nDocument:\n" + source_text,
                "target": reference,
            }
        )
    return rows


def _write_jsonl(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    args = parse_args()
    report_path = Path(args.report_json)
    if not report_path.exists():
        raise SystemExit(f"Report file not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = _extract_rows(report)
    if len(rows) < 2:
        rows = _rows_from_lexglue(Path(args.lexglue_csv), max_rows=args.max_rows)
    if len(rows) < 2:
        raise SystemExit("Not enough rows found from report or LexGLUE fallback to build training data.")

    random.seed(args.seed)
    random.shuffle(rows)

    valid_ratio = max(0.0, min(0.9, float(args.valid_ratio)))
    valid_count = max(1, int(len(rows) * valid_ratio))
    valid_rows = rows[:valid_count]
    train_rows = rows[valid_count:]
    if not train_rows:
        train_rows = valid_rows
        valid_rows = []

    train_out = Path(args.train_out)
    valid_out = Path(args.valid_out)
    _write_jsonl(train_out, train_rows)
    if valid_rows:
        _write_jsonl(valid_out, valid_rows)

    print(f"Train rows: {len(train_rows)} -> {train_out.resolve()}")
    if valid_rows:
        print(f"Valid rows: {len(valid_rows)} -> {valid_out.resolve()}")
    else:
        print("No validation rows written (dataset too small).")


if __name__ == "__main__":
    main()
