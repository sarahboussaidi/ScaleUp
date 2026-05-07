from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image
from torch.utils.data import Dataset
from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    TrOCRProcessor,
    VisionEncoderDecoderModel,
)


class OCRPairDataset(Dataset):
    def __init__(self, rows: List[Tuple[Path, str]], processor: TrOCRProcessor, max_target_length: int = 128):
        self.rows = rows
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> Dict[str, List[int]]:
        image_path, text = self.rows[idx]
        image = Image.open(image_path).convert("RGB")

        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values.squeeze(0)
        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True,
            return_tensors="pt",
        ).input_ids.squeeze(0)

        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        return {
            "pixel_values": pixel_values,
            "labels": labels,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune TrOCR for OCR objective with optional encoder freezing.")
    parser.add_argument("--base-model", default="microsoft/trocr-base-printed")
    parser.add_argument("--train-manifest", required=True, help="JSONL with keys: image_path, text")
    parser.add_argument("--valid-manifest", default=None, help="Optional JSONL validation manifest")
    parser.add_argument("--output-dir", default="models/trocr_finetuned")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-target-length", type=int, default=128)
    parser.add_argument("--freeze-encoder", action="store_true", help="Freeze vision backbone and train decoder head")
    parser.add_argument("--freeze-decoder", action="store_true", help="Freeze decoder (not typical; optional)")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _load_manifest(path: str) -> List[Tuple[Path, str]]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise SystemExit(f"Manifest file not found: {manifest_path}")

    rows: List[Tuple[Path, str]] = []
    with manifest_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                raise SystemExit(f"Invalid JSON at {manifest_path}:{line_no}: {exc}") from exc

            image_value = str(obj.get("image_path", "")).strip()
            text = str(obj.get("text", "")).strip()
            if not image_value or not text:
                continue

            image_path = Path(image_value)
            if not image_path.is_absolute():
                image_path = (manifest_path.parent / image_path).resolve()
            if image_path.exists():
                rows.append((image_path, text))

    if not rows:
        raise SystemExit(f"No valid rows found in manifest: {manifest_path}")
    return rows


def _apply_freeze(model: VisionEncoderDecoderModel, freeze_encoder: bool, freeze_decoder: bool) -> None:
    if freeze_encoder:
        for param in model.encoder.parameters():
            param.requires_grad = False

    if freeze_decoder:
        for param in model.decoder.parameters():
            param.requires_grad = False


def _print_trainable_summary(model: VisionEncoderDecoderModel) -> None:
    total = 0
    trainable = 0
    for p in model.parameters():
        n = p.numel()
        total += n
        if p.requires_grad:
            trainable += n
    pct = (100.0 * trainable / total) if total else 0.0
    print(f"Trainable params: {trainable:,} / {total:,} ({pct:.2f}%)")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_rows = _load_manifest(args.train_manifest)
    valid_rows = _load_manifest(args.valid_manifest) if args.valid_manifest else []

    # Dry-run: validate datasets and exit before loading heavy model weights.
    if args.dry_run:
        print("Dry run passed.")
        print(f"Train samples: {len(train_rows)}")
        print(f"Validation samples: {len(valid_rows) if valid_rows else 0}")
        return

    # Load processor and model only when actually training (avoid large downloads during dry-run).
    processor = TrOCRProcessor.from_pretrained(args.base_model)
    model = VisionEncoderDecoderModel.from_pretrained(args.base_model)

    # Ensure config tokens are set for Seq2Seq generation/training
    if getattr(model.config, "decoder_start_token_id", None) is None:
        model.config.decoder_start_token_id = getattr(processor.tokenizer, "bos_token_id", None)
    if getattr(model.config, "pad_token_id", None) is None:
        model.config.pad_token_id = getattr(processor.tokenizer, "pad_token_id", None)
    if getattr(model.config, "vocab_size", None) is None:
        try:
            model.config.vocab_size = model.config.decoder.vocab_size
        except Exception:
            model.config.vocab_size = len(processor.tokenizer)

    _apply_freeze(model, freeze_encoder=args.freeze_encoder, freeze_decoder=args.freeze_decoder)
    _print_trainable_summary(model)

    train_ds = OCRPairDataset(train_rows, processor, max_target_length=args.max_target_length)
    eval_ds = OCRPairDataset(valid_rows, processor, max_target_length=args.max_target_length) if valid_rows else None

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch" if eval_ds is not None else "no",
        predict_with_generate=True,
        fp16=args.fp16,
        bf16=args.bf16,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=processor,
    )

    trainer.train()
    trainer.save_model(str(out_dir))
    processor.save_pretrained(str(out_dir))

    metadata = {
        "base_model": args.base_model,
        "train_manifest": args.train_manifest,
        "valid_manifest": args.valid_manifest,
        "epochs": args.epochs,
        "freeze_encoder": args.freeze_encoder,
        "freeze_decoder": args.freeze_decoder,
    }
    (out_dir / "finetune_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Fine-tuned OCR model saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
