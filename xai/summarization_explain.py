"""XAI utilities for document summarization: clause confidence and keyword attribution."""
from typing import List, Dict, Any
import re


def clause_confidence_score(clause_text: str, keywords: List[str]) -> float:
    """Compute confidence score for a clause based on keyword matches.
    
    Args:
        clause_text: The extracted clause text
        keywords: List of keywords that triggered the extraction
    
    Returns:
        Confidence score 0..1
    """
    if not clause_text or not keywords:
        return 0.5
    
    text_lower = clause_text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    
    # Confidence based on keyword density and clause length
    keyword_density = matches / len(keywords) if keywords else 0
    
    # Longer clauses with multiple keyword matches = higher confidence
    length_factor = min(1.0, len(clause_text) / 500.0)
    
    confidence = (keyword_density + length_factor) / 2.0
    return min(1.0, max(0.5, confidence))  # Clamp to [0.5, 1.0]


def highlight_keywords_in_clause(clause_text: str, keywords: List[str]) -> str:
    """Return clause with keywords marked for highlighting."""
    highlighted = clause_text
    for kw in keywords:
        # Simple case-insensitive replacement with markers
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pattern.sub(f"[KW]{kw}[/KW]", highlighted)
    return highlighted


def clause_explanation(
    category: str,
    clause_text: str,
    keywords_used: List[str],
    confidence: float
) -> str:
    """Generate readable explanation for why a clause was extracted."""
    keyword_str = ", ".join(keywords_used[:3])
    if len(keywords_used) > 3:
        keyword_str += f", +{len(keywords_used) - 3} more"
    
    return f"Extracted '{category}' clause with {confidence:.0%} confidence. Triggered by keywords: {keyword_str}."


def summarization_explanation_text(
    clauses: List[Dict[str, Any]],
    total_clauses: int
) -> str:
    """Generate overall explanation of document summarization."""
    if not clauses:
        return "No key clauses detected in the document."
    
    avg_conf = sum(c.get('confidence', 0.5) for c in clauses) / len(clauses) if clauses else 0.5
    
    text = f"Extracted {len(clauses)} key clauses from {total_clauses} total sections. "
    text += f"Average extraction confidence: {avg_conf:.1%}. "
    text += "Higher confidence clauses are more likely to be accurately summarized."
    
    return text
