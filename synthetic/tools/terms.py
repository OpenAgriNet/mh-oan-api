"""Search terms tool — uses real glossary_terms.json (no mocking needed)."""

import json
from rapidfuzz import fuzz

# Load real term pairs
term_pairs = json.load(open('assets/glossary_terms.json', 'r', encoding='utf-8'))


async def search_terms(
    term: str,
    max_results: int = 5,
    threshold: float = 0.7,
    language: str = None,
) -> str:
    """Search for terms using fuzzy partial string matching across all fields.

    Args:
        term: The term to search for
        max_results: Maximum number of results to return
        threshold: Minimum similarity score (0-1) to consider a match
        language: Optional language to restrict search to (en/mr/transliteration)

    Returns:
        str: Formatted string with matching results
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    matches = []
    term_lower = term.lower()

    for pair in term_pairs:
        max_score = 0

        if language in [None, "en"]:
            en_score = fuzz.ratio(term_lower, pair.get("en", "").lower()) / 100.0
            max_score = max(max_score, en_score)

        if language in [None, "mr"]:
            mr_score = fuzz.ratio(term_lower, pair.get("mr", "").lower()) / 100.0
            max_score = max(max_score, mr_score)

        if language in [None, "transliteration"]:
            tr_score = fuzz.ratio(term_lower, pair.get("transliteration", "").lower()) / 100.0
            max_score = max(max_score, tr_score)

        if max_score >= threshold:
            matches.append((pair, max_score))

    matches.sort(key=lambda x: x[1], reverse=True)

    if matches:
        matches = matches[:max_results]
        lines = []
        for pair, score in matches:
            lines.append(f"{pair.get('en', '')} -> {pair.get('mr', '')} ({pair.get('transliteration', '')}) [{score:.0%}]")
        return f"Matching Terms for `{term}`\n\n" + "\n".join(lines)
    else:
        return f"No matching terms found for `{term}`"
