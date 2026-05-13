from .utils import SRS_GENERATION_DIR, safe_read_csv, detect_column


def get_generation_xai_summary():
    rag_df = safe_read_csv(SRS_GENERATION_DIR / "rag_references_sample.csv")

    if rag_df.empty:
        return {
            "status": "no_rag_reference_file",
            "message": "No RAG reference file found.",
            "evidence": [],
        }

    text_col = detect_column(rag_df, ["evidence_text", "text", "requirement_text"])
    sim_col = detect_column(rag_df, ["evidence_similarity", "similarity", "score"])
    section_col = detect_column(rag_df, ["section_title", "section", "section_label"])

    evidence = []
    for _, row in rag_df.head(10).iterrows():
        evidence.append(
            {
                "section": str(row.get(section_col, "")) if section_col else "",
                "similarity": float(row.get(sim_col, 0)) if sim_col else 0,
                "evidence_text": str(row.get(text_col, ""))[:300] if text_col else "",
                "explanation": "This example was retrieved as RAG evidence because it is semantically close to the generated SRS section.",
            }
        )

    return {
        "status": "success",
        "message": "RAG evidence XAI summary generated.",
        "evidence": evidence,
    }