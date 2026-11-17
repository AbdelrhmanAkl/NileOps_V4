"""General Bilingual Lexical Support & Overlap Calculation.

Provides general stopword filtering, orthographic token normalization,
and query-to-passage lexical containment scoring for Arabic and English text.
No external network dependencies; purely local, deterministic Python.
"""

import re
from typing import Set, Tuple

# Standard English grammatical stopwords (closed-class function words)
EN_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn", "it", "its",
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "now", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

# Standard Arabic grammatical stopwords (closed-class particles, prepositions, conjunctions, question particles)
AR_STOPWORDS = {
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "تم", "كان", "كانت",
    "هو", "هي", "التي", "الذي", "الذين", "ما", "ماذا", "هل", "كيف", "كم", "أين",
    "متى", "لماذا", "أي", "كل", "بعض", "غير", "بين", "حول", "حيث", "عند", "لدى",
    "أو", "ثم", "بل", "لكن", "لا", "لم", "لن", "ليس", "ليست", "أن", "إن", "إذا",
    "لو", "حتى", "قد", "فقد", "لقد", "إذ", "إلا", "ذلك", "تلك", "هؤلاء", "أولئك",
    "يا", "أنا", "نحن", "أنت", "أنتم", "هم", "هن", "به", "بها", "بهم", "فيه", "فيها",
    "منه", "منها", "عنه", "عنها", "له", "لها", "لهم", "الي", "علي", "اليها", "عليها"
}

ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")


PUNCTUATION_REGEX = re.compile(r"[؟،؛!?:.,()\[\]{}\"\'\-_/\\]")


def normalize_token(token: str) -> str:
    """Normalize a single token orthographically (Arabic and English)."""
    t = token.lower()
    t = PUNCTUATION_REGEX.sub("", t)
    t = ARABIC_DIACRITICS.sub("", t)
    # Normalize Alef forms
    t = re.sub(r"[إأآا]", "ا", t)
    # Normalize Teh Marbuta to Heh
    t = re.sub(r"ة", "ه", t)
    # Normalize Alef Maqsura to Yeh
    t = re.sub(r"ى", "ي", t)
    return t.strip()


def extract_content_tokens(text: str) -> Set[str]:
    """Extract content word tokens and morphological variants (e.g. stripped 'ال' prefix)."""
    if not text:
        return set()
    # Strip punctuation first
    clean_text = PUNCTUATION_REGEX.sub(" ", text)
    raw_tokens = re.findall(r"[\w\u0600-\u06FF]+", clean_text)
    tokens = set()
    for raw in raw_tokens:
        clean = normalize_token(raw)
        if len(clean) < 2:
            continue
        if clean in EN_STOPWORDS or clean in AR_STOPWORDS:
            continue
        tokens.add(clean)
        # In Arabic, allow matching base stem without definite article 'ال'
        if len(clean) >= 4 and clean.startswith("ال"):
            stem = clean[2:]
            if stem not in AR_STOPWORDS and len(stem) >= 2:
                tokens.add(stem)
        # In Arabic, allow matching without conjunction prefix 'و'
        elif len(clean) >= 4 and clean.startswith("و"):
            stem = clean[1:]
            if stem not in AR_STOPWORDS and len(stem) >= 2:
                tokens.add(stem)
    return tokens


def compute_lexical_containment(query: str, doc_text: str) -> float:
    """Compute the fraction of query content tokens present in the document passage."""
    q_tokens = extract_content_tokens(query)
    if not q_tokens:
        return 0.0
    d_tokens = extract_content_tokens(doc_text)
    if not d_tokens:
        return 0.0
    matches = q_tokens.intersection(d_tokens)
    return len(matches) / float(len(q_tokens))
