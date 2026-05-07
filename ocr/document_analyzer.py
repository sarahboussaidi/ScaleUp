from pathlib import Path
from typing import Any, Dict, List, Optional

from objective_registry import get_selected_value


class DocumentAnalyzer:
    def __init__(self, confidence_threshold: float = 0.2, primary_engine: Optional[str] = None):
        self.confidence_threshold = confidence_threshold
        self.primary_engine = (primary_engine or str(get_selected_value("ocr", "primary_engine", "easyocr") or "easyocr")).strip().lower()
        self.keywords = [
            "agreement",
            "termination",
            "liability",
            "payment",
            "penalty",
            "confidential",
            "breach",
            "jurisdiction",
        ]
        self._cv2 = None
        self._easyocr = None
        self._nlp = None
        self._reader = None
        self._original_shape = None
        self._processed_shape = None

    def _iou(self, box_a: List[int], box_b: List[int]) -> float:
        ax1, ay1, aw, ah = box_a
        bx1, by1, bw, bh = box_b
        ax2, ay2 = ax1 + aw, ay1 + ah
        bx2, by2 = bx1 + bw, by1 + bh

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter = inter_w * inter_h
        if inter == 0:
            return 0.0

        area_a = aw * ah
        area_b = bw * bh
        union = max(area_a + area_b - inter, 1)
        return float(inter) / float(union)

    def _box_contains_center(self, outer: List[int], inner: List[int]) -> bool:
        ox, oy, ow, oh = outer
        ix, iy, iw, ih = inner
        cx = ix + (iw // 2)
        cy = iy + (ih // 2)
        return ox <= cx <= (ox + ow) and oy <= cy <= (oy + oh)

    def _normalize_text(self, text: str) -> str:
        cleaned = " ".join(str(text).split())
        cleaned = cleaned.replace("|", "I")
        cleaned = cleaned.replace("ﬁ", "fi")
        cleaned = cleaned.replace("ﬂ", "fl")
        return cleaned.strip()

    def _build_variants(self, image):
        variants = []
        if len(image.shape) == 3:
            gray = self._cv2.cvtColor(image, self._cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        variants.append(("gray", gray))

        denoised = self._cv2.fastNlMeansDenoising(gray, None, 12, 7, 21)
        variants.append(("denoise", denoised))

        clahe = self._cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
        variants.append(("clahe", clahe))

        thresh = self._cv2.adaptiveThreshold(
            clahe,
            255,
            self._cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            self._cv2.THRESH_BINARY,
            31,
            11,
        )
        variants.append(("adaptive", thresh))
        return variants

    def _merge_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        for cand in sorted(candidates, key=lambda r: (-float(r.get("conf", 0.0)), -(len(str(r.get("text", "")))))):
            text = self._normalize_text(str(cand.get("text", "")))
            if not text:
                continue
            cand["text"] = text

            replaced = False
            for i, item in enumerate(merged):
                overlap = self._iou(cand["box"], item["box"])
                near_same = overlap >= 0.22 or self._box_contains_center(item["box"], cand["box"]) or self._box_contains_center(cand["box"], item["box"])
                if near_same:
                    keep_new = (float(cand.get("conf", 0.0)) > float(item.get("conf", 0.0)) + 0.05) or (
                        len(text) > len(str(item.get("text", ""))) + 2
                    )
                    if keep_new:
                        merged[i] = cand
                    replaced = True
                    break
            if not replaced:
                merged.append(cand)

        def sort_key(item):
            x, y, _, _ = item["box"]
            return (round(y / 14), x)

        return sorted(merged, key=sort_key)

    def _extract_tesseract_candidates(self, image, scale_x: float, scale_y: float) -> List[Dict[str, Any]]:
        try:
            import pytesseract  # type: ignore
        except Exception:
            return []

        if len(image.shape) == 3:
            gray = self._cv2.cvtColor(image, self._cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        config = "--oem 3 --psm 6"
        data = pytesseract.image_to_data(gray, config=config, output_type='dict')
        out: List[Dict[str, Any]] = []

        for i in range(len(data.get('text', []))):
            text = self._normalize_text(data['text'][i])
            if not text:
                continue
            try:
                conf_value = float(data['conf'][i]) / 100.0
            except Exception:
                conf_value = 0.0
            if conf_value < max(self.confidence_threshold, 0.55):
                continue
            if len(text) < 3 and conf_value < 0.8:
                continue

            x = int(float(data['left'][i]) * scale_x)
            y = int(float(data['top'][i]) * scale_y)
            w = int(float(data['width'][i]) * scale_x)
            h = int(float(data['height'][i]) * scale_y)
            if w <= 2 or h <= 2:
                continue
            out.append(
                {
                    "text": text,
                    "polygon": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                    "box": [x, y, w, h],
                    "conf": conf_value,
                }
            )

        return out

    def _load_dependencies(self) -> None:
        if self._cv2 is None:
            import cv2  # type: ignore

            self._cv2 = cv2
        if self._easyocr is None:
            import easyocr  # type: ignore

            self._easyocr = easyocr
        if self._reader is None:
            self._reader = self._easyocr.Reader(["en"])
        if self._nlp is None:
            import spacy  # type: ignore

            self._nlp = spacy.load("en_core_web_sm")

    def load_image(self, image_path: str):
        self._load_dependencies()
        img = self._cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Image not found: {image_path}")
        return img

    def preprocess(self, img):
        gray = self._cv2.cvtColor(img, self._cv2.COLOR_BGR2GRAY)
        # Store original and processed shape for scaling
        self._original_shape = img.shape[:2][::-1]  # (width, height)
        gray = self._cv2.resize(gray, None, fx=2, fy=2, interpolation=self._cv2.INTER_CUBIC)
        self._processed_shape = gray.shape[:2][::-1]  # (width, height)
        return gray

    def extract_text_with_boxes(self, image) -> List[Dict[str, Any]]:
        self._load_dependencies()

        from ocr.multi_ocr_engine import MultiOCREngine

        if len(image.shape) == 3:
            original = image
            processed = self.preprocess(image)
        else:
            processed = image
            if self._original_shape is None:
                h, w = image.shape[:2]
                self._original_shape = (w, h)
                self._processed_shape = (w, h)
            original = None

        if self._original_shape is None or self._processed_shape is None:
            h, w = processed.shape[:2]
            self._original_shape = (w, h)
            self._processed_shape = (w, h)

        scale_x = self._original_shape[0] / max(self._processed_shape[0], 1)
        scale_y = self._original_shape[1] / max(self._processed_shape[1], 1)

        engine = MultiOCREngine(primary_engine=self.primary_engine)

        def _quality_score(text: str) -> float:
            value = (text or "").strip()
            if not value:
                return 0.0
            letters = sum(1 for ch in value if ch.isalpha())
            digits = sum(1 for ch in value if ch.isdigit())
            alpha_ratio = letters / max(len(value), 1)
            digit_penalty = min(0.2, digits / max(len(value), 1))
            tokens = ["".join(ch for ch in tok.lower() if ch.isalnum()) for tok in value.split()]
            tokens = [t for t in tokens if t]
            if not tokens:
                return 0.0
            longish = [t for t in tokens if len(t) >= 3]
            vowelish = [t for t in longish if any(v in t for v in "aeiou")]
            lexical_ratio = len(vowelish) / max(len(longish), 1)
            return max(0.0, min(1.0, (0.55 * alpha_ratio) + (0.45 * lexical_ratio) - digit_penalty))

        def _normalize_rows(rows):
            out = []
            for item in rows:
                text = str(item.get("text", "")).strip()
                if not text:
                    continue
                box = item.get("box", [0, 0, 0, 0])
                out.append({
                    "text": text,
                    "box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                    "conf": float(item.get("confidence", item.get("conf", 0.0)) or 0.0),
                })
            return out

        all_results = engine.extract_all(processed)
        best_rows = []
        best_score = -1.0
        for rows in all_results.values():
            if not isinstance(rows, list):
                continue
            norm = _normalize_rows(rows)
            if not norm:
                continue
            joined = " ".join(r["text"] for r in norm)
            quality = _quality_score(joined)
            avg_conf = sum(r["conf"] for r in norm) / max(len(norm), 1)
            score = (0.6 * quality) + (0.4 * avg_conf)
            if score > best_score:
                best_score = score
                best_rows = norm

        ocr_candidates = best_rows
        if not ocr_candidates:
            raw = engine.extract(processed)
            ocr_candidates = _normalize_rows(raw)

        adjusted: List[Dict[str, Any]] = []
        for item in ocr_candidates:
            x, y, w, h = item["box"]
            x = int(x * scale_x)
            y = int(y * scale_y)
            w = max(1, int(w * scale_x))
            h = max(1, int(h * scale_y))
            adjusted.append(
                {
                    "text": item["text"],
                    "box": [x, y, w, h],
                    "polygon": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                    "conf": float(item.get("conf", 0.0)),
                }
            )

        return self._merge_candidates(adjusted)

    def is_important(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def highlight_image(self, img, ocr_results: List[Dict[str, Any]]):
        img_copy = img.copy()
        import numpy as np
        for item in ocr_results:
            text = item["text"]
            if self.is_important(text):
                color = (0, 0, 255)
                thickness = 2
            else:
                color = (0, 255, 0)
                thickness = 1
            # Draw polygon if available, else fallback to rectangle
            if "polygon" in item:
                pts = np.array([item["polygon"]], dtype=np.int32)
                self._cv2.polylines(img_copy, [pts], isClosed=True, color=color, thickness=thickness)
            else:
                x, y, w, h = item["box"]
                self._cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, thickness)
        return img_copy

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        doc = self._nlp(text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    def analyze(self, image_path: str, save_annotated_to: Optional[str] = None) -> Dict[str, Any]:
        img = self.load_image(image_path)
        ocr_results = self.extract_text_with_boxes(img)
        # Reconstruct text with line breaks based on vertical position
        lines = []
        last_y = None
        line = []
        heights = [item["box"][3] for item in ocr_results] if ocr_results else [20]
        line_gap = max(12, int((sum(heights) / max(len(heights), 1)) * 0.65))
        for item in ocr_results:
            y = item["box"][1]
            if last_y is not None and abs(y - last_y) > line_gap:
                lines.append(" ".join(line))
                line = []
            line.append(item["text"])
            last_y = y
        if line:
            lines.append(" ".join(line))
        full_text = "\n".join(lines)
        entities = self.extract_entities(full_text)

        output: Dict[str, Any] = {
            "text": full_text,
            "entities": entities,
            "ocr_results": ocr_results,
            "keyword_hits": [item["text"] for item in ocr_results if self.is_important(item["text"])],
        }

        if save_annotated_to:
            highlighted = self.highlight_image(img, ocr_results)
            output_path = Path(save_annotated_to)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._cv2.imwrite(str(output_path), highlighted)
            output["annotated_image_path"] = str(output_path)

        return output
