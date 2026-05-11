"""
pitch_generator.py
------------------
Loads your fine-tuned model from Hugging Face Hub and generates
pitch deck slides + exports a .pptx file.

Usage: imported by app.py via /pitch routes
"""

import os
import torch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# ── HuggingFace model config ─────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL = os.path.join(BASE_DIR, "models", "pitch_deck_final")

# ── Slide tasks ───────────────────────────────────────────────────────────────
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

# ── Global model state (loaded once) ─────────────────────────────────────────
_model     = None
_tokenizer = None


def load_model():
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    print(f"[PitchGen] Loading model from local folder: {LOCAL_MODEL}")
    has_gpu = torch.cuda.is_available()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL, local_files_only=True)

    if has_gpu:
        from transformers import BitsAndBytesConfig
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        _model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL,
            quantization_config=quant_config,
            device_map="auto",
            local_files_only=True,
        )
        print("[PitchGen] Model loaded on GPU ✅")
    else:
        _model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True,
            local_files_only=True,
        )
        print("[PitchGen] Model loaded on CPU ✅ (generation will be slow)")

    _model.eval()
    return _model, _tokenizer

# ── Text cleaning ─────────────────────────────────────────────────────────────
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


# ── Slide generation ──────────────────────────────────────────────────────────
def generate_slide(company: str, industry: str, description: str, slide_type: str) -> str:
    model, tokenizer = load_model()

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
