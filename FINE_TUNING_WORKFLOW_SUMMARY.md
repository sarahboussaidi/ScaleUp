# Fine-Tuning Workflow Summary

Date: 2026-05-06

## What Was Added
- `fine_tune_legal_llama.py`: LoRA fine-tuning entrypoint for legal instruction data with model-architecture-aware target modules.
- `fine_tune_ocr_trocr.py`: TrOCR fine-tuning entrypoint with encoder/decoder freeze support and training-compatibility fixes for the installed `transformers` version.
- `prepare_legal_instruction_data.py`: Generates legal instruction JSONL data.
- `prepare_ocr_manifest.py`: Generates OCR training/validation manifests.
- `ocr/multi_ocr_engine.py`: Added support for loading a fine-tuned TrOCR engine.
- `legal_document_intelligence.py`: Added local causal-LM routing for on-device inference.
- `train_signature_yolo.py`: Added YOLO freeze and training options.

## Smoke Validation Results
- LLaMA smoke run completed successfully with `gpt2` on `data/legal_train_small.jsonl` and `data/legal_valid_small.jsonl`.
- TrOCR smoke run completed successfully on `data/ocr_train_small.jsonl` and `data/ocr_valid_small.jsonl`.
- Both runs produced checkpoints under `models/`.

## Artifacts
- `models/llama_smoke`
- `models/trocr_smoke`
- `data/legal_train_small.jsonl`
- `data/legal_valid_small.jsonl`
- `data/ocr_train_small.jsonl`
- `data/ocr_valid_small.jsonl`

## Notes
- The LLaMA smoke run required adjusting LoRA target modules for GPT-2 compatibility.
- The installed `transformers` version uses `eval_strategy` and `processing_class` instead of older argument names in the trainer APIs.
- The TrOCR model config needed `decoder_start_token_id` and `pad_token_id` set explicitly before training.
