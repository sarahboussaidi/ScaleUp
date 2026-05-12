
import os
import json
import faiss
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoTokenizer, AutoModelForCausalLM


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


sdg_names = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals"
}


def load_rag_system(base_dir):
    rag_dir = os.path.join(base_dir, "rag_index")
    embedding_dir = os.path.join(base_dir, "embedding_model")
    sdg_dir = os.path.join(base_dir, "sdg_distilbert")

    index = faiss.read_index(os.path.join(rag_dir, "sustainability_faiss.index"))

    with open(os.path.join(rag_dir, "chunks_metadata.json"), "r", encoding="utf-8") as f:
        chunks = json.load(f)

    embedding_model = SentenceTransformer(embedding_dir)

    sdg_tokenizer = AutoTokenizer.from_pretrained(sdg_dir)
    sdg_classifier = AutoModelForSequenceClassification.from_pretrained(sdg_dir)
    sdg_classifier.to(DEVICE)
    sdg_classifier.eval()

    return {
        "index": index,
        "chunks": chunks,
        "embedding_model": embedding_model,
        "sdg_tokenizer": sdg_tokenizer,
        "sdg_classifier": sdg_classifier
    }


def predict_sdgs_from_text(text, rag_system, top_k=3, max_length=256):
    tokenizer = rag_system["sdg_tokenizer"]
    model = rag_system["sdg_classifier"]

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length
    )

    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]

    top_scores, top_indices = torch.topk(probs, k=top_k)

    predicted_sdgs = []

    for score, idx in zip(top_scores, top_indices):
        sdg_number = int(idx.item()) + 1
        predicted_sdgs.append({
            "sdg": f"SDG {sdg_number}: {sdg_names[sdg_number]}",
            "confidence": float(score)
        })

    return predicted_sdgs


def retrieve_context(query, rag_system, top_k=10):
    embedding_model = rag_system["embedding_model"]
    index = rag_system["index"]
    chunks = rag_system["chunks"]

    query_embedding = embedding_model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    retrieved_chunks = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        chunk = chunks[idx]

        retrieved_chunks.append({
            "source": chunk.get("source", "unknown"),
            "chunk_id": chunk.get("chunk_id", int(idx)),
            "text": chunk.get("text", ""),
            "distance": float(dist)
        })

    return retrieved_chunks


def filter_retrieved_chunks_by_predicted_sdgs(retrieved_chunks, predicted_sdgs):
    allowed_numbers = []

    for sdg_item in predicted_sdgs:
        sdg = sdg_item["sdg"] if isinstance(sdg_item, dict) else sdg_item
        number = sdg.split(":")[0].replace("SDG", "").strip()
        allowed_numbers.append(number)

    filtered = []

    for chunk in retrieved_chunks:
        text = chunk["text"].strip()

        if text.startswith("SDG "):
            keep = any(text.startswith(f"SDG {num} ") for num in allowed_numbers)
            if keep:
                filtered.append(chunk)
        else:
            filtered.append(chunk)

    return filtered


def build_rag_prompt(bmc_text, predicted_sdgs, retrieved_chunks):
    predicted_sdgs_text = "\n".join([
        f"- {item['sdg']} ({item['confidence']:.2f})"
        if isinstance(item, dict)
        else f"- {item}"
        for item in predicted_sdgs
    ])

    retrieved_text = "\n\n".join([
        f"[CHUNK {i+1} | SOURCE FILE: {chunk['source']}]\n{chunk['text']}"
        for i, chunk in enumerate(retrieved_chunks)
    ])

    prompt = f"""
You are a sustainable business model expert.

Your task is to improve the following Business Model Canvas using the retrieved sustainability knowledge.

BUSINESS MODEL CANVAS:
{bmc_text}

PREDICTED SDGs:
{predicted_sdgs_text}

RETRIEVED KNOWLEDGE:
{retrieved_text}

Instructions:
- Suggest eco-friendly and sustainable improvements.
- Link improvements to relevant SDGs.
- Keep the answer clear and structured.
- Mention only the retrieved source file names when using external knowledge.
- Do not invent fake sources.
"""

    return prompt


def load_qwen_model(model_name="Qwen/Qwen2.5-1.5B-Instruct"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )

    model.eval()

    return tokenizer, model


def generate_with_qwen(prompt, tokenizer, model, max_new_tokens=1200):
    messages = [
        {
            "role": "system",
            "content": "You are a sustainability and business model expert."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )

    return response.strip()


def run_full_rag_pipeline(bmc_text, rag_system, qwen_tokenizer, qwen_model, top_k_sdgs=3, top_k_chunks=10):
    predicted_sdgs = predict_sdgs_from_text(
        bmc_text,
        rag_system,
        top_k=top_k_sdgs
    )

    query = (
        bmc_text
        + " sustainability carbon emissions circular economy green logistics energy efficiency waste reduction "
        + " ".join([item["sdg"] for item in predicted_sdgs])
    )

    retrieved_chunks = retrieve_context(
        query,
        rag_system,
        top_k=top_k_chunks
    )

    retrieved_chunks = filter_retrieved_chunks_by_predicted_sdgs(
        retrieved_chunks,
        predicted_sdgs
    )

    retrieved_chunks = retrieved_chunks[:7]

    prompt = build_rag_prompt(
        bmc_text,
        predicted_sdgs,
        retrieved_chunks
    )

    response = generate_with_qwen(
        prompt,
        qwen_tokenizer,
        qwen_model,
        max_new_tokens=1400
    )

    return {
        "predicted_sdgs": predicted_sdgs,
        "retrieved_chunks": retrieved_chunks,
        "prompt": prompt,
        "eco_suggestions": response
    }
