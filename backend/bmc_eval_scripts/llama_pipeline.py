"""
bmc/llama_pipeline.py
Step 4 — LLaMA Unified Pipeline
Handles OCR selection, RAG retrieval, and LLaMA evaluation for all 9 sections.
Returns a JSON-contract-compliant dict.
"""

import os
import json
import pickle
from pathlib import Path
from PIL import Image

ADAPTER_DIR = Path("bmc_eval_models/llama_bmc_adapter")
FAISS_INDEX = ADAPTER_DIR / "bmc_faiss_index.faiss"
CHUNKS_PKL = ADAPTER_DIR / "bmc_text_chunks.pkl"
BASE_MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"  # adjust if different
TOP_K_RAG = 3


class LLamaBMCPipeline:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.faiss_index = None
        self.chunks = None
        self.embedder = None

    def load(self):
        if self.model is not None:
            return

        import torch
        import faiss
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        from peft import PeftModel
        from sentence_transformers import SentenceTransformer
        from dotenv import load_dotenv

        load_dotenv()
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise EnvironmentError("HF_TOKEN not set in .env")

        # Load tokenizer + base model + LoRA adapter
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(ADAPTER_DIR), token=hf_token
        )
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(load_in_4bit=True)

        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            token=hf_token,
            quantization_config=bnb_config,
            device_map="auto",
        )
        self.model = PeftModel.from_pretrained(base, str(ADAPTER_DIR), assign=True)
        self.model.eval()

        # Load RAG index and chunks
        self.faiss_index = faiss.read_index(str(FAISS_INDEX))
        with open(CHUNKS_PKL, "rb") as f:
            self.chunks = pickle.load(f)

        # Sentence embedder for RAG queries
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # ── OCR ──────────────────────────────────────────────────────────────────

    def _ocr_printed(self, image: Image.Image) -> str:
        import pytesseract
        return pytesseract.image_to_string(image).strip()

    def _ocr_handwritten(self, image: Image.Image) -> str:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        import torch

        processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
        trocr = VisionEncoderDecoderModel.from_pretrained(
            "microsoft/trocr-base-handwritten"
        )
        pixel_values = processor(image.convert("RGB"), return_tensors="pt").pixel_values
        with torch.no_grad():
            ids = trocr.generate(pixel_values)
        return processor.batch_decode(ids, skip_special_tokens=True)[0].strip()

    def _ocr(self, image: Image.Image, text_type: str) -> str:
        if text_type == "handwritten":
            return self._ocr_handwritten(image)
        return self._ocr_printed(image)

    # ── RAG ──────────────────────────────────────────────────────────────────

    def _retrieve(self, query: str) -> str:
        embedding = self.embedder.encode([query], convert_to_numpy=True)
        _, indices = self.faiss_index.search(embedding, TOP_K_RAG)
        retrieved = [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
        return "\n\n".join(chunk["text"] for chunk in retrieved)

    # ── LLaMA evaluation ─────────────────────────────────────────────────────

    def _evaluate_section(self, section_name: str, text: str, context: str) -> dict:
        """
        Returns {"score": int, "feedback": str, "suggestions": [str, str]}
        """
        prompt = (
            f"You are a Business Model Canvas expert.\n\n"
            f"Relevant knowledge:\n{context}\n\n"
            f"BMC Section: {section_name}\n"
            f"Content: {text}\n\n"
            f"Evaluate this section. Reply ONLY with a JSON object with keys:\n"
            f"score (0-100 int), feedback (str), suggestions (list of 2 strings)."
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        import torch
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                temperature=1.0,
            )
        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()

        try:
            # Strip markdown fences if present
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"score": 50, "feedback": response, "suggestions": []}

    def _evaluate_coherence(self, boxes: list[dict]) -> dict:
        summary = "\n".join(
            f"{b['name']}: {b['content'][:200]}" for b in boxes
        )
        prompt = (
            f"You are a BMC expert. Evaluate the overall coherence of this BMC:\n\n"
            f"{summary}\n\n"
            f"Reply ONLY with JSON: score (0-100), feedback (str), suggestions (list of 2 strings)."
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        import torch
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=200, do_sample=False, temperature=1.0)
        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"score": 50, "feedback": response, "suggestions": []}

    def _evaluate_sustainability(self, boxes: list[dict]) -> dict:
        summary = "\n".join(
            f"{b['name']}: {b['content'][:150]}" for b in boxes
        )
        prompt = (
            f"You are a BMC sustainability advisor. Evaluate sustainability of this BMC:\n\n"
            f"{summary}\n\n"
            f"Reply ONLY with JSON: feedback (str), suggestions (list of 2 strings)."
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        import torch
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=200, do_sample=False, temperature=1.0)
        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"feedback": response, "suggestions": []}

    # ── Main entry ────────────────────────────────────────────────────────────

    def run(self, sections: list[dict]) -> dict:
        """
        sections: list of dicts with keys: id, name, crop (PIL.Image), text_type
        Returns the full JSON-contract-compliant result dict.
        """
        self.load()

        boxes = []
        scores = []

        for section in sections:
            text = self._ocr(section["crop"], section["text_type"])
            context = self._retrieve(f"{section['name']}: {text}")
            evaluation = self._evaluate_section(section["name"], text, context)

            score = int(evaluation.get("score", 50))
            scores.append(score)

            boxes.append({
                "id": section["id"],
                "name": section["name"],
                "score": score,
                "content": text,
                "feedback": evaluation.get("feedback", ""),
                "suggestions": evaluation.get("suggestions", []),
            })

        overall_score = round(sum(scores) / len(scores)) if scores else 0
        coherence = self._evaluate_coherence(boxes)
        sustainability = self._evaluate_sustainability(boxes)

        # Derive strengths / weaknesses from scores
        sorted_boxes = sorted(boxes, key=lambda b: b["score"], reverse=True)
        strengths = [b["name"] for b in sorted_boxes[:3]]
        weaknesses = [b["name"] for b in sorted_boxes[-2:]]

        return {
            "overallScore": overall_score,
            "boxes": boxes,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "coherence": coherence,
            "sustainability": sustainability,
        }


# Module-level singleton
_pipeline = LLamaBMCPipeline()


def run(sections: list[dict]) -> dict:
    return _pipeline.run(sections)