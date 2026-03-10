"""
Prompt quality tests for MahaVistaar system prompts.

Runs single-turn conversations with the agrinet agent across all 3 languages
and checks the response against quality criteria:
  - Language purity (no code-mixing)
  - Source citation correctness (no internal tools cited)
  - Formatting (no over-bolding, no quotes around terms)
  - Response length within bounds
  - Follows response templates

Usage:
    python -m synthetic.test_prompts [--lang mr|hi|en] [--verbose]
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from uuid import uuid4

from synthetic.agrinet import agrinet_agent
from synthetic.deps import FarmerContext
from synthetic.moderation import moderation_agent
from synthetic.user import generate_random_profile


# ---------------------------------------------------------------------------
# Test queries per language
# ---------------------------------------------------------------------------

TEST_QUERIES = {
    "mr": [
        ("कापसावर बोंड अळीचा प्रादुर्भाव झाला आहे, काय करावे?", "crop_pest"),
        ("पुणे जिल्ह्याचा हवामान अंदाज सांगा", "weather"),
        ("सोलापूर मंडीत कांद्याचे भाव काय आहेत?", "mandi"),
        ("पीएम किसान योजनेची माहिती द्या", "scheme"),
        ("जवळचे KVK केंद्र कुठे आहे?", "services"),
    ],
    "hi": [
        ("कपास में बॉलवर्म का प्रकोप हुआ है, क्या करें?", "crop_pest"),
        ("पुणे जिले का मौसम पूर्वानुमान बताइए", "weather"),
        ("सोलापुर मंडी में प्याज के भाव क्या हैं?", "mandi"),
        ("पीएम किसान योजना की जानकारी दीजिए", "scheme"),
        ("नजदीकी KVK केंद्र कहाँ है?", "services"),
    ],
    "en": [
        ("Bollworm attack on my cotton crop, what should I do?", "crop_pest"),
        ("What is the weather forecast for Pune district?", "weather"),
        ("What are onion prices in Solapur mandi?", "mandi"),
        ("Tell me about PM Kisan scheme", "scheme"),
        ("Where is the nearest KVK center?", "services"),
    ],
}

# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------

# Internal tools that should NEVER appear in source citations
INTERNAL_TOOL_PATTERNS = [
    r"forward.?geocod",
    r"reverse.?geocod",
    r"search.?terms",
    r"fetch.?agristack",
    r"location.?lookup",
    r"geocod(?:e|ing)",
]

# English words that indicate code-mixing in mr/hi responses
# (common agricultural terms that should be in Devanagari)
# Exclude words that appear in source citations (**स्रोत: ...**) or tool-returned names
ENGLISH_LEAK_PATTERNS = [
    r"\b(?:crop|irrigation|fertilizer|pesticide|disease|scheme|weather|forecast|market|price|soil|seed|harvest|sowing|variety|application|eligibility)\b",
]

# Over-bolding: bold words that are NOT section headers, scheme names, amounts, or sources
# We check for bold patterns that don't match allowed categories
BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
ALLOWED_BOLD_PATTERNS = [
    r"^(मिट्टी|माती|मृदा|जमीन|Soil):?$",           # Soil header
    r"^(किस्में|वाण|जाती|Varieties):?$",              # Varieties header
    r"^(खाद|खत|Fertilizer).*:?$",                     # Fertilizer header
    r"^(कीट|कीड|Pest).*:?$",                          # Pest header
    r"^(सिंचाई|सिंचन|Irrigation):?$",                 # Irrigation header
    r"^(मौसम|हवामान|Weather|खेती सलाह|शेती सल्ला|Farming advice):?$",
    r"^(पात्रता|Eligibility):?$",
    r"^(आवेदन|अर्ज|How to apply).*:?$",
    r"^(लाभ|Benefits?):?$",                            # Benefits header
    r"^(आवश्यक|Required).*:?$",                       # Required docs header
    r"^स्रोत:.*$",                                     # Source citation
    r"^Source:.*$",
    r"₹",                                              # Amounts
    r"योजना",                                          # Scheme names (any with योजना)
    r"Yojana",                                         # English scheme names
    r"^(प्रधानमंत्री|मुख्यमंत्री|राष्ट्रीय)",          # Scheme name prefixes
    r"^(PM|PMFBY|PMKSY|PM-KISAN|Pradhan)",             # English scheme abbreviations/names
    r"^(बुवाई|रोपाई|Sowing):?$",
    r"^(कटाई|Harvesting):?$",
    r"^(जलवायु|Climate):?$",
    r"^(एकात्मिक|समन्वित|Integrated).*:?$",           # IPM headers
    r"^(पता|निगरानी|Monitor).*:?$",                    # Monitoring headers
    r"\.gov\.",                                         # Government URLs
    r"pmkisan",                                        # PM Kisan portal
    r"(KVK|केव्हीके|केवीके|कृषी विज्ञान|कृषि विज्ञान|Krishi Vigyan)", # KVK names
    r"(CHC|सीएचसी|Custom Hiring)",                     # CHC names
    r"(महाडीबीटी|MahaDBT|सेवा केंद्र|CSC)",             # Service center names
    r"(कार्यालय|Office|केंद्र|Center|Centre)",          # Office/center names
    r"^(Shri|श्री|सुश्री|Mrs|Mr)\.?",                   # Officer names
    r"^\d{10}$",                                        # Phone numbers
    r"^(जमीनधारक|शेतकरी|किसान)",                        # Farmer category descriptors in scheme context
]


def check_language_purity(response: str, lang: str) -> list[str]:
    """Check for English code-mixing in non-English responses."""
    issues = []
    if lang == "en":
        return issues

    # Strip source citation lines before checking — tool-returned names may be English
    lines = response.split("\n")
    non_source_lines = [l for l in lines if not re.match(r"\s*\*\*\s*(स्रोत|Source)\s*:", l)]
    text_to_check = "\n".join(non_source_lines)

    for pattern in ENGLISH_LEAK_PATTERNS:
        matches = re.findall(pattern, text_to_check, re.IGNORECASE)
        if matches:
            issues.append(f"Code-mixing: found English word(s) {matches} in {lang} response")
    return issues


def check_source_citations(response: str) -> list[str]:
    """Check that no internal/utility tools are cited as sources."""
    issues = []
    for pattern in INTERNAL_TOOL_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Internal tool cited as source: matched pattern '{pattern}'")
    return issues


def check_formatting(response: str) -> list[str]:
    """Check for over-bolding and quote usage."""
    issues = []

    # Check for quoted terms (backticks in user-facing text are a clear violation)
    backticked = re.findall(r"`([^`]{2,})`", response)
    # Filter out source citation backticks which may be in prompt template examples
    backticked = [b for b in backticked if not b.startswith("**")]
    if backticked:
        issues.append(f"Backtick-quoted terms found (should write naturally): {backticked[:5]}")

    # Check for over-bolding
    bold_matches = BOLD_PATTERN.findall(response)
    for match in bold_matches:
        match_stripped = match.strip()
        if not any(re.search(p, match_stripped) for p in ALLOWED_BOLD_PATTERNS):
            # Check if it's a reasonable section header (ends with colon or is short)
            if not (match_stripped.endswith(":") and len(match_stripped) < 30):
                issues.append(f"Potentially over-bolded: **{match_stripped}**")

    return issues


def check_response_length(response: str) -> list[str]:
    """Check that the response is within expected sentence bounds."""
    issues = []
    sentences = [s.strip() for s in re.split(r"[.।!?]", response) if s.strip() and len(s.strip()) > 10]
    if len(sentences) > 15:
        issues.append(f"Response too long: {len(sentences)} sentences (max ~10)")
    return issues


def check_has_source(response: str, query_type: str) -> list[str]:
    """Check that factual responses include a source citation."""
    issues = []
    if query_type in ("crop_pest", "weather", "mandi", "scheme", "services"):
        if not re.search(r"\*\*\s*स्रोत\s*:|Source\s*:", response, re.IGNORECASE):
            # Don't flag if response is a clarifying question (asking for location, etc.)
            clarifying_patterns = [
                r"(कृपया|कृपा करून|please|which|कोणत|कौन|किस).*(जिल्हा|जिला|तालुका|district|taluka|village|गाव|स्थान|location|नाव|नाम)",
                r"(लिहा|लिखें|बताएँ|बता दें|send|tell me|share)",
                r"(उपलब्ध नाही|उपलब्ध नहीं|not available|not found|down|temporarily)",
            ]
            is_clarifying = any(re.search(p, response, re.IGNORECASE) for p in clarifying_patterns)
            if not is_clarifying and len(response) > 150:
                issues.append("Missing source citation for factual response")
    return issues


def check_no_capability_hallucination(response: str) -> list[str]:
    """Check that agent doesn't ask for photos, links, maps, etc."""
    issues = []
    hallucination_patterns = [
        (r"(?:photo|फोटो|छायाचित्र|तस्वीर|फ़ोटो).*(?:भेज|send|upload|अपलोड|पाठव)", "Asks for photo upload"),
        (r"google\s*maps", "Mentions Google Maps"),
        (r"plus\s*code", "Asks for plus code"),
        (r"screenshot|स्क्रीनशॉट", "Asks for screenshot"),
        (r"(?:link|लिंक).*(?:भेज|send|share|शेयर|पाठव)", "Asks for links"),
    ]
    for pattern, desc in hallucination_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Capability hallucination: {desc}")
    return issues


def check_follow_up_question(response: str) -> list[str]:
    """Check that response ends with a follow-up question."""
    issues = []
    # Check last 200 chars for a question mark — the response may have trailing whitespace
    tail = response.strip()[-200:]
    if "?" not in tail and "का?" not in tail:
        issues.append("Response does not end with a follow-up question")
    return issues


ALL_CHECKS = [
    ("Language purity", check_language_purity),
    ("Source citations", check_source_citations),
    ("Formatting", check_formatting),
    ("Response length", check_response_length),
    ("Has source", check_has_source),
    ("No capability hallucination", check_no_capability_hallucination),
    ("Follow-up question", check_follow_up_question),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_single_test(query: str, query_type: str, lang: str, verbose: bool = False) -> dict:
    """Run one query through the agrinet agent and check quality."""

    profile = generate_random_profile(language=lang)
    now = datetime.now()

    farmer_ctx = FarmerContext(
        query=query,
        lang_code=lang,
        session_id=str(uuid4()),
        today_date=now,
        moderation_str="**Moderation Compliance:** Proceed (Valid Agricultural)",
        farmer_id=profile.farmer_id if profile.has_agristack else None,
        farmer_name=profile.name,
        farmer_phone=profile.phone,
        farmer_state=profile.state,
        farmer_district=profile.district,
        farmer_taluka=profile.taluka,
        farmer_village=profile.village,
        farmer_village_code=profile.village_code,
        farmer_crops=profile.crops,
        farmer_land_acres=profile.land_acres,
        farmer_gender=profile.gender,
        farmer_caste_category=profile.caste_category,
        farmer_latitude=profile.latitude,
        farmer_longitude=profile.longitude,
        farmer_is_pocra=profile.is_pocra,
    )

    try:
        result = await agrinet_agent.run(
            user_prompt=farmer_ctx.get_user_message(),
            deps=farmer_ctx,
        )
        response = result.output
    except Exception as e:
        return {
            "query": query,
            "lang": lang,
            "query_type": query_type,
            "error": str(e),
            "passed": False,
            "issues": [f"Agent error: {e}"],
            "response": "",
        }

    # Run all checks
    all_issues = []
    for check_name, check_fn in ALL_CHECKS:
        if check_name == "Language purity":
            issues = check_fn(response, lang)
        elif check_name == "Has source":
            issues = check_fn(response, query_type)
        else:
            issues = check_fn(response)
        all_issues.extend(issues)

    return {
        "query": query,
        "lang": lang,
        "query_type": query_type,
        "passed": len(all_issues) == 0,
        "issues": all_issues,
        "response": response,
    }


async def run_tests(languages: list[str], verbose: bool = False):
    """Run all prompt quality tests."""
    total = 0
    passed = 0
    failed = 0
    results = []

    for lang in languages:
        queries = TEST_QUERIES.get(lang, [])
        print(f"\n{'='*60}")
        print(f"  Testing {lang.upper()} prompts ({len(queries)} queries)")
        print(f"{'='*60}")

        for query, query_type in queries:
            total += 1
            print(f"\n[{lang}/{query_type}] {query[:60]}...")

            result = await run_single_test(query, query_type, lang, verbose)
            results.append(result)

            if result["passed"]:
                passed += 1
                print(f"  PASS")
            else:
                failed += 1
                print(f"  FAIL")
                for issue in result["issues"]:
                    print(f"    - {issue}")

            if verbose:
                print(f"\n  Response:\n  {'-'*50}")
                for line in result["response"].split("\n"):
                    print(f"  {line}")
                print(f"  {'-'*50}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'='*60}")

    if failed > 0:
        print("\nFailed tests:")
        for r in results:
            if not r["passed"]:
                print(f"  [{r['lang']}/{r['query_type']}] {r['query'][:50]}")
                for issue in r["issues"]:
                    print(f"    - {issue}")

    # Save detailed results
    output_path = "data/prompt_test_results.json"
    try:
        from pathlib import Path
        Path("data").mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nDetailed results saved to {output_path}")
    except Exception as e:
        print(f"\nCould not save results: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Test MahaVistaar system prompt quality")
    parser.add_argument("--lang", choices=["mr", "hi", "en", "all"], default="all",
                        help="Language(s) to test (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full responses")
    args = parser.parse_args()

    if args.lang == "all":
        languages = ["mr", "hi", "en"]
    else:
        languages = [args.lang]

    asyncio.run(run_tests(languages, args.verbose))


if __name__ == "__main__":
    main()
