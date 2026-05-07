from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a local LLaMA-style model on legal instruction data.")
    parser.add_argument("--model", required=True, help="Base model path or HF model id")
    parser.add_argument("--train-file", required=True, help="JSONL/CSV file with instruction data")
    parser.add_argument("--valid-file", default=None, help="Optional validation file")
    parser.add_argument("--output-dir", default="models/llama_legal_finetuned")
    parser.add_argument("--text-column", default="text", help="Column containing full prompt+target text")
    parser.add_argument("--prompt-column", default="prompt", help="Prompt column (used if text-column missing)")
    parser.add_argument("--target-column", default="target", help="Target/answer column")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--freeze-base", action="store_true", help="Freeze base model weights and train LoRA adapters only")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _read_dataset(path: str, split_name: str) -> Dataset:
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(f"Dataset file not found: {file_path}")
    ext = file_path.suffix.lower()
    if ext == ".jsonl":
        return load_dataset("json", data_files=str(file_path), split="train")
    if ext == ".json":
        return load_dataset("json", data_files=str(file_path), split="train")
    if ext == ".csv":
        return load_dataset("csv", data_files=str(file_path), split="train")
    raise SystemExit(f"Unsupported dataset extension: {ext}. Use .jsonl, .json, or .csv")


def _build_text(example: Dict[str, str], text_column: str, prompt_column: str, target_column: str) -> str:
    if text_column in example and str(example.get(text_column, "")).strip():
        return str(example[text_column])

    prompt = str(example.get(prompt_column, "")).strip()
    target = str(example.get(target_column, "")).strip()
    if not prompt or not target:
        return ""

    return (
        "### Instruction:\n"
        f"{prompt}\n\n"
        "### Response:\n"
        f"{target}"
    )


def _tokenize_dataset(
    dataset: Dataset,
    tokenizer: AutoTokenizer,
    max_length: int,
    text_column: str,
    prompt_column: str,
    target_column: str,
) -> Dataset:
    def _format_and_tokenize(batch: Dict[str, List[str]]) -> Dict[str, List[List[int]]]:
        texts: List[str] = []
        for i in range(len(next(iter(batch.values())))):
            row = {k: batch[k][i] for k in batch.keys()}
            txt = _build_text(row, text_column, prompt_column, target_column)
            texts.append(txt)

        encoded = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )
        encoded["labels"] = [ids[:] for ids in encoded["input_ids"]]
        return encoded

    tokenized = dataset.map(_format_and_tokenize, batched=True)
    tokenized = tokenized.filter(lambda ex: any(v != tokenizer.pad_token_id for v in ex["input_ids"]))
    keep_cols = {"input_ids", "attention_mask", "labels"}
    drop_cols = [c for c in tokenized.column_names if c not in keep_cols]
    return tokenized.remove_columns(drop_cols)


def _prepare_model(args: argparse.Namespace):
    dtype = None
    if args.bf16:
        dtype = torch.bfloat16
    elif args.fp16:
        dtype = torch.float16

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=dtype,
        device_map="auto",
    )

    # Choose sensible default LoRA target modules based on the base model architecture.
    model_type = getattr(model.config, "model_type", "").lower()
    if "llama" in model_type or "vicuna" in model_type or "mpt" in model_type:
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    elif "gpt2" in model_type or "gpt" in model_type:
        target_modules = ["c_attn", "c_proj"]
    else:
        # Fallback to a conservative set that works for many causal models; may need tuning per model.
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

    lora_cfg = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=target_modules,
        task_type="CAUSAL_LM",
    )

    try:
        model = get_peft_model(model, lora_cfg)
    except ValueError as e:
        raise ValueError(f"Failed to apply LoRA to model '{args.model}': {e}\nCheck `target_modules` for this architecture.")

    if args.freeze_base:
        for name, param in model.named_parameters():
            if "lora_" not in name:
                param.requires_grad = False

    model.print_trainable_parameters()
    return model


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_ds = _read_dataset(args.train_file, "train")
    valid_ds = _read_dataset(args.valid_file, "validation") if args.valid_file else None

    tokenized_train = _tokenize_dataset(
        train_ds,
        tokenizer,
        args.max_length,
        args.text_column,
        args.prompt_column,
        args.target_column,
    )
    tokenized_valid = (
        _tokenize_dataset(
            valid_ds,
            tokenizer,
            args.max_length,
            args.text_column,
            args.prompt_column,
            args.target_column,
        )
        if valid_ds is not None
        else None
    )

    if args.dry_run:
        print("Dry run passed.")
        print(f"Train samples: {len(tokenized_train)}")
        print(f"Valid samples: {len(tokenized_valid) if tokenized_valid is not None else 0}")
        return

    model = _prepare_model(args)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    training_args = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch" if tokenized_valid is not None else "no",
        bf16=args.bf16,
        fp16=args.fp16,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_valid,
        data_collator=collator,
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))

    metadata = {
        "base_model": args.model,
        "train_file": args.train_file,
        "valid_file": args.valid_file,
        "epochs": args.epochs,
        "max_length": args.max_length,
        "freeze_base": args.freeze_base,
        "lora": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
        },
    }
    (out_dir / "finetune_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Fine-tuned model saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
