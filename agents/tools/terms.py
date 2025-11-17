import json
from enum import Enum
from pydantic import BaseModel, Field
from rapidfuzz import fuzz

# Load term pairs from JSON file with UTF-8 encoding
term_pairs = json.load(open('assets/glossary_terms.json', 'r', encoding='utf-8'))

class Language(str, Enum):
    ENGLISH = "en"
    MARATHI = "mr"
    TRANSLITERATION = "transliteration"

class TermPair(BaseModel):
    en: str = Field(description="English term")
    mr: str = Field(description="Marathi term")
    transliteration: str = Field(description="Transliteration of Marathi term to English")

    def __str__(self):
        return f"{self.en} -> {self.mr} ({self.transliteration})"

# Convert raw dictionaries to TermPair objects
TERM_PAIRS = [TermPair(**pair) for pair in term_pairs]

async def search_terms(
    term: str, 
    max_results: int = 5,
    threshold: float = 0.7,
    language: Language = None
) -> str:
    """Search for terms using fuzzy partial string matching across all fields.
    
    Args:
        term: The term to search for
        max_results: Maximum number of results to return
        threshold: Minimum similarity score (0-1) to consider a match (default is 0.7)
        language: Optional language to restrict search to (en/mr/transliteration)
        
    Returns:
        str: Formatted string with matching results and their scores
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
        
    matches = []
    term = term.lower()
    
    for term_pair in TERM_PAIRS:
        max_score = 0
        
        # Check English term if no language specified or language is English
        if language in [None, Language.ENGLISH]:
            en_score = fuzz.ratio(term, term_pair.en.lower()) / 100.0
            max_score = max(max_score, en_score)
            
        # Check Marathi term if no language specified or language is Marathi    
        if language in [None, Language.MARATHI]:
            mr_score = fuzz.ratio(term, term_pair.mr.lower()) / 100.0
            max_score = max(max_score, mr_score)
            
        # Check transliteration if no language specified or language is transliteration
        if language in [None, Language.TRANSLITERATION]:
            tr_score = fuzz.ratio(term, term_pair.transliteration.lower()) / 100.0
            max_score = max(max_score, tr_score)
            
        if max_score >= threshold:
            matches.append((term_pair, max_score))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)    
    
    if len(matches) > 0:
        matches = matches[:max_results]
        return f"Matching Terms for `{term}`\n\n" + "\n".join([f"{match[0]} [{match[1]:.0%}]" for match in matches])
    else:
        return f"No matching terms found for `{term}`"


### Utility functions for Correcting Document Search Results

import re
from rapidfuzz import process

# Build English index from glossary
EN_INDEX = {tp.en.lower(): tp for tp in TERM_PAIRS}
EN_TERMS = list(EN_INDEX.keys())

def build_glossary_pattern(terms):
    """
    Build a regex alternation pattern for glossary terms.
    Longer terms first to ensure multi-word phrases
    (e.g., 'Yellow Mosaic Virus') are matched before 'Virus'.
    """
    sorted_terms = sorted(terms, key=len, reverse=True)
    escaped = [re.escape(t) for t in sorted_terms]
    return r"\b(" + "|".join(escaped) + r")\b"

# Precompile regex pattern once
GLOSSARY_PATTERN = re.compile(build_glossary_pattern(EN_TERMS), flags=re.IGNORECASE)

def normalize_text_with_glossary(text: str, threshold=97):
    """
    Append Marathi term in brackets next to English glossary terms. Preserves formatting & avoids spacing issues.
    NOTE: Adds about 100ms of latency to the search results. Can it be optimized?
    """

    def replacer(match):
        word = match.group(0)
        lw = word.lower().strip()

        # Exact match
        if lw in EN_INDEX:
            marathi = EN_INDEX[lw].mr
        else:
            # Fuzzy fallback (very high threshold to avoid false positives)
            match_term, score, _ = process.extractOne(
                lw, EN_TERMS, score_cutoff=threshold
            ) or (None, 0, None)
            if not match_term:
                return word
            marathi = EN_INDEX[match_term].mr

        # Decide spacing: if next char is alphanumeric, add space after replacement
        after = match.end()
        if after < len(text) and text[after].isalnum():
            return f"{word} [{marathi}] "
        else:
            return f"{word} [{marathi}]"

    return GLOSSARY_PATTERN.sub(replacer, text)