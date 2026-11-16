"""Arabic & English Query Normalization Service.

Provides general orthographic preprocessing for queries before dense semantic vector retrieval in Qdrant.
Applies general normalization (stripping diacritics/tashkeel, normalizing whitespace) without injecting
any question-derived keywords, synthetic synonyms, or heuristic phrase substitutions.
"""

import re


def normalize_colloquial_query(query: str) -> str:
    """Normalize query text using general orthographic rules.
    
    Removes Arabic diacritics (tashkeel) and collapses whitespace.
    Does not use question-derived synonyms or keyword injection lists.
    """
    if not query:
        return ""
    
    text = query.strip()
    # Strip Arabic diacritics (tashkeel: Fatha, Damma, Kasra, Sukun, Tanween, Shadda)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Collapse excess whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
