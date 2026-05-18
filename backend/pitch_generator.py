"""
pitch_generator.py
------------------
Loads your fine-tuned model from the LOCAL pitch_deck_final/ folder
and generates pitch deck slides + exports a .pptx file.
"""

import os
import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer

# Optional: use Hugging Face InferenceClient when available for better retries
try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL = os.path.join(BASE_DIR, "models", "pitch_deck_final")

SLIDE_TASKS = {
    "problem":        "Write a problem slide. Who has the problem, what is the pain, why does it matter.",
    "solution":       "Write a solution slide. What the product does, how it works, key differentiator.",
    "market":         "Write a market slide. Who is the target market and why now.",
    "product":        "Write a product slide. Core features and how users use it.",
    "business_model": "Write a business model slide. How the company makes money.",
    "competition":    "Write a competition slide. Alternatives and why this product wins.",
    "team":           "Write a team slide. Why this team can build it.",
    "ask":            "Write an ask slide. What support, funding, or partners are needed.",
}

SYSTEM = (
    "You are an expert pitch deck writer. "
    "Generate investor-ready slide content. "
    "Be specific and credible. Do not invent fake numbers."
)

_model     = None
_tokenizer = None
_load_attempted = False

def load_model():
    global _model, _tokenizer, _load_attempted

    if _model is not None:
        return _model, _tokenizer
    if _load_attempted:
        return None, None

    _load_attempted = True

    print(f"[PitchGen] Loading model from: {LOCAL_MODEL}")

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    try:
        _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL, local_files_only=True)

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        offload_dir = os.path.join(BASE_DIR, "offload")
        os.makedirs(offload_dir, exist_ok=True)

        # Strategy 1: aggressive offload with device_map='auto' and CPU fp32 offload
        try:
            print("[PitchGen] Attempting model load: 4-bit + device_map='auto' + offload + fp32_cpu_offload")
            _model = AutoModelForCausalLM.from_pretrained(
                LOCAL_MODEL,
                quantization_config=quant_config,
                device_map="auto",
                offload_folder=offload_dir,
                offload_state_dict=True,
                low_cpu_mem_usage=True,
                llm_int8_enable_fp32_cpu_offload=True,
                local_files_only=True,
            )
            print("[PitchGen] Model loaded with offload ✅")
            _model.eval()
            return _model, _tokenizer
        except Exception as e1:
            print(f"[PitchGen] Strategy 1 failed: {e1}")

        # Strategy 2: force CPU with low_cpu_mem_usage and enable fp32 CPU offload
        try:
            print("[PitchGen] Attempting model load: 4-bit + device_map='cpu' + low_cpu_mem_usage + fp32_cpu_offload")
            _model = AutoModelForCausalLM.from_pretrained(
                LOCAL_MODEL,
                quantization_config=quant_config,
                device_map="cpu",
                low_cpu_mem_usage=True,
                llm_int8_enable_fp32_cpu_offload=True,
                local_files_only=True,
            )
            print("[PitchGen] Model loaded on CPU ✅")
            _model.eval()
            return _model, _tokenizer
        except Exception as e2:
            print(f"[PitchGen] Strategy 2 failed: {e2}")

        # Strategy 3: try without 4-bit quantization (fallback)
        try:
            print("[PitchGen] Attempting model load: full-precision fallback (no 4-bit)")
            quant_config.load_in_4bit = False
            _model = AutoModelForCausalLM.from_pretrained(
                LOCAL_MODEL,
                low_cpu_mem_usage=True,
                device_map="auto",
                local_files_only=True,
            )
            print("[PitchGen] Full-precision model loaded ✅")
            _model.eval()
            return _model, _tokenizer
        except Exception as e3:
            print(f"[PitchGen] Strategy 3 failed: {e3}")

        # If all strategies fail, fall back to template generator
        print("[PitchGen] All model load strategies failed, falling back to template generator")
        _model = None
        _tokenizer = None
        return _model, _tokenizer
    except Exception as e:
        print(f"[PitchGen] Tokenizer/model prep failed: {e}")
        _model = None
        _tokenizer = None
        return _model, _tokenizer
BAD_STOPS = [
    "SYSTEM:", "USER:", "Company:", "Startup:", "Name:",
    "Industry:", "Description:", "Rules:", "Write the",
    "ASSISTANT:", "Task:", "Slide:", "Question:", "Answer:",
]

def clean_output(text: str) -> str:
    for stop in BAD_STOPS:
        if stop in text:
            text = text[: text.index(stop)]
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 15:
            continue
        if line.lower().startswith(
            ("problem", "solution", "market", "team", "ask",
             "product", "traction", "competition", "business")
        ):
            continue
        lines.append(line)
    result = " ".join(lines)
    sentences = result.split(". ")
    return ". ".join(sentences[:3]).strip()


def generate_slide(company: str, industry: str, description: str, slide_type: str) -> str:
    # Do NOT call load_model() here to avoid repeated expensive load attempts.
    # The caller should call load_model() once via generate_all_slides().
    model = _model
    tokenizer = _tokenizer

    HF_API_TOKEN = os.getenv("HF_API_TOKEN")
    HF_MODEL = os.getenv("HF_MODEL", "didina01/pitch-deck-phi3")

    # Try to use InferenceClient if available (better error handling)
    def _hf_generate(prompt: str) -> str:
        if not HF_API_TOKEN:
            return ""
        # Prefer InferenceClient when installed
        try:
            if InferenceClient is not None:
                client = InferenceClient(token=HF_API_TOKEN)
                # text_generation returns a list of dicts with 'generated_text'
                out = client.text_generation(model=HF_MODEL, inputs=prompt, max_new_tokens=80, temperature=0.4, top_p=0.8)
                if isinstance(out, list) and out:
                    return out[0].get("generated_text") or out[0].get("text") or ""
                if isinstance(out, dict):
                    return out.get("generated_text") or out.get("text") or ""
                return ""
        except Exception as e:
            print(f"[PitchGen] InferenceClient call failed: {e}")

        # Fallback to direct REST call
        try:
            url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 80,
                    "temperature": 0.4,
                    "top_p": 0.8,
                    "return_full_text": False,
                },
                "options": {"wait_for_model": True},
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text") or data[0].get("text") or ""
            if isinstance(data, dict):
                return data.get("generated_text") or data.get("text") or ""
        except Exception as e:
            print(f"[PitchGen] HF inference failed: {e}")
        return ""

    def _fallback(slide_type: str, company: str, industry: str, description: str) -> str:
        # Simple rule-based fallback to guarantee output when the model can't be loaded.
        desc = description.strip()
        sentences = [s.strip() for s in desc.replace('\n', ' ').split('. ') if s.strip()]
        first = sentences[0] if sentences else f"{company} provides a solution in {industry}."
        if slide_type == 'problem':
            return f"{company} addresses: {first}."
        if slide_type == 'solution':
            return f"Solution: {first}."
        if slide_type == 'market':
            return f"Target market: {industry} — {first}."
        if slide_type == 'product':
            return f"Product: {first}."
        if slide_type == 'business_model':
            return f"Business model: {first}."
        if slide_type == 'competition':
            return f"Competition: alternatives exist, {company} differentiates by {first}."
        if slide_type == 'team':
            return f"Team: experienced founders with domain knowledge in {industry}."
        if slide_type == 'ask':
            return f"Ask: seeking partners and resources to scale {company}."
        return first

    if model is None or tokenizer is None:
        # Try remote HF inference using the uploaded model if token available
        prompt = (
            f"SYSTEM: {SYSTEM}\n\n"
            f"Startup:\nName: {company}\nIndustry: {industry}\n"
            f"Description: {description}\n\n"
            f"Write the {slide_type} slide.\n\n"
            "Rules:\n"
            "- Use only information from the description\n"
            "- No fake investors or funding numbers\n"
            "- Maximum 3 sentences\n"
            "- Output only the slide content\n\n"
            "ASSISTANT:\n"
        )
        if HF_API_TOKEN:
            raw = _hf_generate(prompt)
            cleaned = clean_output(raw)
            if cleaned and len(cleaned) > 20:
                return cleaned
        return _fallback(slide_type, company, industry, description)

    prompt = (
        f"SYSTEM: {SYSTEM}\n\n"
        f"Startup:\nName: {company}\nIndustry: {industry}\n"
        f"Description: {description}\n\n"
        f"Write the {slide_type} slide.\n\n"
        "Rules:\n"
        "- Use only information from the description\n"
        "- No fake investors or funding numbers\n"
        "- Maximum 3 sentences\n"
        "- Output only the slide content\n\n"
        "ASSISTANT:\n"
    )

    device = next(model.parameters()).device
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=400,
    ).to(device)

    best = ""
    for _ in range(3):
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.4,
                top_p=0.8,
                do_sample=True,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
        raw = tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        cleaned = clean_output(raw)
        if cleaned and len(cleaned) > 30:
            best = cleaned
            break

    return best if best else f"{company} — {slide_type} content."


def generate_all_slides(company: str, industry: str, description: str) -> dict:
    # Try one model load attempt at startup to avoid repeated expensive failures.
    load_model()
    slides = {}
    for slide_type in SLIDE_TASKS:
        print(f"[PitchGen] Generating: {slide_type}...")
        slides[slide_type] = generate_slide(company, industry, description, slide_type)
    return slides


# ── PPTX export ───────────────────────────────────────────────────────────────
C = {
    "bg_dark":  RGBColor(0x1E, 0x27, 0x61),
    "bg_light": RGBColor(0xF4, 0xF6, 0xFF),
    "accent":   RGBColor(0x4A, 0x90, 0xD9),
    "white":    RGBColor(0xFF, 0xFF, 0xFF),
    "dark_txt": RGBColor(0x1E, 0x27, 0x61),
    "body_txt": RGBColor(0x33, 0x3A, 0x5C),
    "muted":    RGBColor(0x88, 0x92, 0xB0),
}

SLIDE_ORDER = [
    ("problem",        "The Problem"),
    ("solution",       "Our Solution"),
    ("market",         "Market Opportunity"),
    ("product",        "Product"),
    ("business_model", "Business Model"),
    ("competition",    "Competition"),
    ("team",           "Team"),
    ("ask",            "The Ask"),
]


def _add_cover(prs, company, industry, tagline=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = C["bg_dark"]

    shape = slide.shapes.add_shape(1, Inches(7.5), Inches(-0.3), Inches(3.0), Inches(3.0))
    shape.fill.solid()
    shape.fill.fore_color.rgb = C["accent"]
    shape.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(1.5), Inches(7.0), Inches(1.4))
    p = tb.text_frame.paragraphs[0]
    p.text = company.upper()
    p.font.size = Pt(52)
    p.font.bold = True
    p.font.color.rgb = C["white"]
    p.font.name = "Arial Black"

    badge = slide.shapes.add_shape(1, Inches(0.6), Inches(3.2), Inches(2.5), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = C["accent"]
    badge.line.fill.background()

    tb2 = slide.shapes.add_textbox(Inches(0.62), Inches(3.22), Inches(2.46), Inches(0.41))
    p2 = tb2.text_frame.paragraphs[0]
    p2.text = industry.upper()
    p2.font.size = Pt(11)
    p2.font.bold = True
    p2.font.color.rgb = C["white"]
    p2.font.name = "Arial"

    if tagline:
        tb3 = slide.shapes.add_textbox(Inches(0.6), Inches(3.9), Inches(8.0), Inches(0.8))
        p3 = tb3.text_frame.paragraphs[0]
        p3.text = tagline[:120]
        p3.font.size = Pt(15)
        p3.font.color.rgb = C["muted"]
        p3.font.name = "Calibri"
        p3.font.italic = True


def _add_content_slide(prs, slide_num, section_title, content):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = C["bg_light"]

    bar = slide.shapes.add_shape(1, Inches(0.4), Inches(0.3), Inches(0.07), Inches(0.75))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C["accent"]
    bar.line.fill.background()

    sn = slide.shapes.add_textbox(Inches(9.2), Inches(0.2), Inches(0.8), Inches(0.4))
    p = sn.text_frame.paragraphs[0]
    p.text = f"0{slide_num}"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C["accent"]
    p.font.name = "Arial Black"

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.25), Inches(8.5), Inches(0.8))
    p = tb.text_frame.paragraphs[0]
    p.text = section_title
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = C["dark_txt"]
    p.font.name = "Arial Black"

    card = slide.shapes.add_shape(1, Inches(0.4), Inches(1.25), Inches(9.2), Inches(3.8))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    card.line.color.rgb = RGBColor(0xCA, 0xDC, 0xFC)
    card.line.width = Pt(1)

    card_top = slide.shapes.add_shape(1, Inches(0.4), Inches(1.25), Inches(9.2), Inches(0.07))
    card_top.fill.solid()
    card_top.fill.fore_color.rgb = C["accent"]
    card_top.line.fill.background()

    tb2 = slide.shapes.add_textbox(Inches(0.7), Inches(1.55), Inches(8.6), Inches(3.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = content
    p2.font.size = Pt(16)
    p2.font.color.rgb = C["body_txt"]
    p2.font.name = "Calibri"


def build_pptx(company: str, industry: str, description: str, slides: dict, output_path: str):
    prs = Presentation()
    prs.slide_width  = Inches(10)
    prs.slide_height = Inches(5.625)

    _add_cover(prs, company, industry, description)

    for idx, (slide_type, section_title) in enumerate(SLIDE_ORDER, start=1):
        content = slides.get(slide_type, "")
        _add_content_slide(prs, idx, section_title, content)

    prs.save(output_path)
    print(f"[PitchGen] Saved: {output_path}")

if __name__ == "__main__":
    import sys, json, traceback

    company = sys.argv[1] if len(sys.argv) > 1 else "Your Startup"
    industry = sys.argv[2] if len(sys.argv) > 2 else "Tech"
    description = sys.argv[3] if len(sys.argv) > 3 else "A great product"

    slides = None
    try:
        slides = generate_all_slides(company, industry, description)
    except Exception as e:
        # If anything unexpected fails, log the traceback and fall back to simple templates
        print(f"[PitchGen][ERROR] generation failed: {e}")
        traceback.print_exc()
        slides = {}
        for st in SLIDE_TASKS.keys():
            slides[st] = (f"{company} — {st} (fallback).")

    # Always output JSON and exit cleanly so callers (API) can parse the result.
    try:
        print(json.dumps(slides))
    except Exception:
        # As a last resort, ensure at least a simple JSON is printed
        safe = {k: str(v) for k, v in (slides or {}).items()}
        print(json.dumps(safe))
