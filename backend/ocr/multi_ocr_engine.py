"""Multi-OCR engine with accuracy tracking and comparison."""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from objective_registry import get_selected_value


class MultiOCREngine:
    """Unified interface for multiple OCR engines with accuracy tracking."""
    
    # Supported OCR engines
    ENGINES = ["easyocr", "paddle", "tesseract", "trocr_finetuned"]
    
    def __init__(self, primary_engine: str = "easyocr"):
        """Initialize multi-OCR engine.
        
        Args:
            primary_engine: Which engine to use by default ('easyocr', 'paddle', or 'tesseract')
        """
        if primary_engine not in self.ENGINES:
            raise ValueError(f"Unknown engine: {primary_engine}. Use one of {self.ENGINES}")
        
        self.primary_engine = primary_engine
        self._engines = {}
        self._accuracy_log = []
        self._load_accuracy_log()
    
    def _load_accuracy_log(self):
        """Load previous accuracy scores from file."""
        log_file = Path(__file__).parent / "ocr_accuracy_log.jsonl"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self._accuracy_log.append(json.loads(line))
            except Exception as e:
                print(f"Warning: Could not load accuracy log: {e}")
    
    def _save_accuracy_log(self):
        """Save accuracy scores to file for tracking."""
        log_file = Path(__file__).parent / "ocr_accuracy_log.jsonl"
        with open(log_file, 'a') as f:
            if self._accuracy_log:
                last = self._accuracy_log[-1]
                f.write(json.dumps(last) + '\n')
    
    def _get_easyocr_engine(self):
        """Lazy-load EasyOCR."""
        if 'easyocr' not in self._engines:
            try:
                import easyocr
                self._engines['easyocr'] = {
                    'reader': easyocr.Reader(["en"]),
                    'name': 'EasyOCR'
                }
            except ImportError:
                raise ImportError("easyocr not installed. Install with: pip install easyocr")
        return self._engines['easyocr']
    
    def _get_paddle_engine(self):
        """Lazy-load PaddleOCR."""
        if 'paddle' not in self._engines:
            try:
                from paddleocr import PaddleOCR
                self._engines['paddle'] = {
                    'reader': PaddleOCR(use_angle_cls=True, lang='en'),
                    'name': 'PaddleOCR'
                }
            except ImportError:
                raise ImportError("paddleocr not installed. Install with: pip install paddleocr")
        return self._engines['paddle']
    
    def _get_tesseract_engine(self):
        """Lazy-load Tesseract."""
        if 'tesseract' not in self._engines:
            try:
                import pytesseract
                self._engines['tesseract'] = {
                    'reader': pytesseract,
                    'name': 'Tesseract'
                }
            except ImportError:
                raise ImportError("pytesseract not installed. Install with: pip install pytesseract")
        return self._engines['tesseract']

    def _resolve_trocr_model_path(self) -> Path:
        selected = get_selected_value("ocr", "model_path", None)
        if selected:
            p = Path(str(selected)).expanduser()
            if not p.is_absolute():
                p = (Path(__file__).resolve().parent.parent / p).resolve()
            if p.exists():
                return p

        env_model = os.getenv("OCR_FINETUNED_MODEL_PATH", "").strip()
        if env_model:
            p = Path(env_model).expanduser()
            if p.exists():
                return p

        default_path = Path(__file__).resolve().parent.parent / "models" / "trocr_finetuned"
        return default_path

    def _get_trocr_engine(self):
        """Lazy-load a fine-tuned TrOCR model."""
        if 'trocr_finetuned' not in self._engines:
            try:
                from transformers import TrOCRProcessor, VisionEncoderDecoderModel
                import torch
            except ImportError as exc:
                raise ImportError(
                    "TrOCR engine requires transformers and torch. Install with: pip install transformers torch"
                ) from exc

            model_path = self._resolve_trocr_model_path()
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Fine-tuned TrOCR model not found at: {model_path}. "
                    "Run fine_tune_ocr_trocr.py first or set OCR_FINETUNED_MODEL_PATH."
                )

            processor = TrOCRProcessor.from_pretrained(str(model_path))
            model = VisionEncoderDecoderModel.from_pretrained(str(model_path))

            if torch.cuda.is_available():
                device = torch.device("cuda")
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = torch.device("mps")
            else:
                device = torch.device("cpu")

            model.to(device)
            model.eval()
            self._engines['trocr_finetuned'] = {
                'processor': processor,
                'model': model,
                'device': device,
                'name': 'TrOCR Fine-Tuned',
                'model_path': str(model_path),
            }
        return self._engines['trocr_finetuned']
    
    def extract_easyocr(self, image) -> List[Dict[str, Any]]:
        """Extract text using EasyOCR."""
        import numpy as np
        engine = self._get_easyocr_engine()
        reader = engine['reader']
        
        # EasyOCR expects BGR or RGB array
        results = reader.readtext(image)
        ocr_results = []
        
        for (bbox, text, conf) in results:
            if conf < 0.3:
                continue
            # Convert bbox (list of 4 points) to bounding box
            x_coords = [pt[0] for pt in bbox]
            y_coords = [pt[1] for pt in bbox]
            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))
            
            ocr_results.append({
                "text": str(text).strip(),
                "confidence": float(conf),
                "box": [x_min, y_min, x_max - x_min, y_max - y_min],
                "engine": "easyocr"
            })
        
        return sorted(ocr_results, key=lambda x: x['box'][1])
    
    def extract_paddle(self, image) -> List[Dict[str, Any]]:
        """Extract text using PaddleOCR."""
        engine = self._get_paddle_engine()
        reader = engine['reader']

        # PaddleOCR API varies by version; try compatible call sequence.
        results = None
        try:
            results = reader.ocr(image, cls=True)
        except TypeError:
            try:
                results = reader.ocr(image)
            except Exception:
                results = reader.predict(image)
        ocr_results = []

        # Newer PaddleOCR (OCRResult list with dict-like items)
        if isinstance(results, list) and results and isinstance(results[0], dict):
            item = results[0]
            polys = item.get('dt_polys') or item.get('rec_polys') or []
            texts = item.get('rec_texts') or []
            scores = item.get('rec_scores') or []
            for bbox, text, conf in zip(polys, texts, scores):
                conf = float(conf)
                if conf < 0.3:
                    continue
                x_coords = [pt[0] for pt in bbox]
                y_coords = [pt[1] for pt in bbox]
                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))
                ocr_results.append({
                    "text": str(text).strip(),
                    "confidence": conf,
                    "box": [x_min, y_min, x_max - x_min, y_max - y_min],
                    "engine": "paddle"
                })

        # Legacy PaddleOCR format: list of [bbox, (text, conf)]
        elif isinstance(results, list) and results and isinstance(results[0], list):
            for line in results[0]:
                bbox = line[0]
                text = line[1][0]
                conf = float(line[1][1])
                if conf < 0.3:
                    continue
                x_coords = [pt[0] for pt in bbox]
                y_coords = [pt[1] for pt in bbox]
                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))
                ocr_results.append({
                    "text": str(text).strip(),
                    "confidence": conf,
                    "box": [x_min, y_min, x_max - x_min, y_max - y_min],
                    "engine": "paddle"
                })
        
        return sorted(ocr_results, key=lambda x: x['box'][1])
    
    def extract_tesseract(self, image) -> List[Dict[str, Any]]:
        """Extract text using Tesseract."""
        import numpy as np
        import cv2
        engine = self._get_tesseract_engine()
        pytesseract = engine['reader']
        
        # Tesseract via pytesseract
        try:
            data = pytesseract.image_to_data(image, output_type='dict')
            ocr_results = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if not text or data['conf'][i] < 30:
                    continue
                
                ocr_results.append({
                    "text": text,
                    "confidence": float(data['conf'][i]) / 100.0,
                    "box": [
                        data['left'][i],
                        data['top'][i],
                        data['width'][i],
                        data['height'][i]
                    ],
                    "engine": "tesseract"
                })
            
            return sorted(ocr_results, key=lambda x: x['box'][1])
        except Exception as e:
            raise RuntimeError(f"Tesseract extraction failed: {e}")

    def extract_trocr_finetuned(self, image) -> List[Dict[str, Any]]:
        """Extract text using a fine-tuned TrOCR model.

        TrOCR is sequence-level OCR, so the output is a single merged line item.
        """
        import numpy as np
        from PIL import Image
        import torch

        engine = self._get_trocr_engine()
        processor = engine['processor']
        model = engine['model']
        device = engine['device']

        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray(image[:, :, ::-1] if image.shape[2] == 3 else image)
        else:
            pil_image = image.convert("RGB")

        pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values.to(device)
        generated_ids = model.generate(pixel_values, max_new_tokens=256)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        w, h = pil_image.size

        if not text:
            return []

        return [
            {
                "text": text,
                "confidence": 0.85,
                "box": [0, 0, w, h],
                "engine": "trocr_finetuned",
            }
        ]
    
    def extract_all(self, image, skip_engines: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Extract text using all available engines.
        
        Args:
            image: Input image array
            skip_engines: List of engines to skip
        
        Returns:
            Dict mapping engine names to their results
        """
        skip_engines = skip_engines or []
        results = {}
        
        for engine_name in self.ENGINES:
            if engine_name in skip_engines:
                continue
            
            try:
                if engine_name == "easyocr":
                    results['easyocr'] = self.extract_easyocr(image)
                elif engine_name == "paddle":
                    results['paddle'] = self.extract_paddle(image)
                elif engine_name == "tesseract":
                    results['tesseract'] = self.extract_tesseract(image)
                elif engine_name == "trocr_finetuned":
                    results['trocr_finetuned'] = self.extract_trocr_finetuned(image)
            except Exception as e:
                results[engine_name] = {"error": str(e)}
        
        return results
    
    def extract(self, image) -> List[Dict[str, Any]]:
        """Extract text using the primary engine."""
        if self.primary_engine == "easyocr":
            return self.extract_easyocr(image)
        elif self.primary_engine == "paddle":
            return self.extract_paddle(image)
        elif self.primary_engine == "tesseract":
            return self.extract_tesseract(image)
        elif self.primary_engine == "trocr_finetuned":
            return self.extract_trocr_finetuned(image)
    
    def set_primary_engine(self, engine_name: str):
        """Switch to a different primary engine."""
        if engine_name not in self.ENGINES:
            raise ValueError(f"Unknown engine: {engine_name}")
        self.primary_engine = engine_name
    
    def record_accuracy(self, engine: str, image_name: str, manual_text: str, extracted_text: str, accuracy_score: float):
        """Record accuracy metrics for an engine.
        
        Args:
            engine: Engine name
            image_name: Source image name
            manual_text: Ground truth text
            extracted_text: OCR-extracted text
            accuracy_score: 0.0 to 1.0 accuracy
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "engine": engine,
            "image": image_name,
            "manual_text": manual_text,
            "extracted_text": extracted_text,
            "accuracy": accuracy_score
        }
        self._accuracy_log.append(entry)
        self._save_accuracy_log()
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Get aggregate accuracy statistics by engine."""
        stats = {}
        for entry in self._accuracy_log:
            engine = entry.get('engine')
            accuracy = entry.get('accuracy', 0)
            
            if engine not in stats:
                stats[engine] = {'scores': [], 'count': 0, 'avg': 0}
            
            stats[engine]['scores'].append(accuracy)
            stats[engine]['count'] += 1
        
        # Calculate averages
        for engine in stats:
            scores = stats[engine]['scores']
            stats[engine]['avg'] = sum(scores) / len(scores) if scores else 0
            stats[engine]['min'] = min(scores) if scores else 0
            stats[engine]['max'] = max(scores) if scores else 0
        
        return stats
    
    def get_accuracy_log(self, engine: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get accuracy log entries."""
        entries = self._accuracy_log
        if engine:
            entries = [e for e in entries if e.get('engine') == engine]
        return entries[-limit:]
