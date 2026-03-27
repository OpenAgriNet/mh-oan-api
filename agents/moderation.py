from pydantic import BaseModel, Field
from typing import Literal
from helpers.utils import get_prompt
from agents.models import MODERATION_CLIENT
import os
import re


class QueryModerationResult(BaseModel):
    """Moderation result of the query."""
    category: Literal[
        "valid_agricultural",
        "invalid_language",
        "invalid_non_agricultural",
        "invalid_external_reference",
        "invalid_compound_mixed",
        "unsafe_illegal",
        "political_controversial",
        "cultural_sensitive",
        "role_obfuscation"
    ] = Field(..., description="Moderation category of the user's message.")
    action: str = Field(..., description="Action to take on the query, always in English.")

    def __str__(self):
        category_str = self.category.replace("_", " ").title()
        return f"**Moderation Recommendation:** {self.action} ({category_str})"


_MODERATION_MODEL_NAME = os.getenv('MODERATION_MODEL_NAME')

ACTION_MAP = {
    "valid_agricultural":         "Proceed with the query",
    "invalid_non_agricultural":   "Decline with standard non-agri response",
    "invalid_external_reference": "Decline with external reference response",
    "invalid_compound_mixed":     "Decline with mixed content response",
    "invalid_language":           "Decline with language policy response",
    "cultural_sensitive":         "Decline with cultural sensitivity response",
    "unsafe_illegal":             "Decline with safety policy response",
    "political_controversial":    "Decline with political neutrality response",
    "role_obfuscation":           "Decline with agricultural-only response",
}

VALID_CATEGORIES = set(ACTION_MAP.keys())


def _parse_moderation_response(raw: str) -> QueryModerationResult:
    """
    Parse the model output into QueryModerationResult.

    Expected format from prompt:
        Category: valid_agricultural Action: Proceed with the query
    """
    raw = raw.strip()

    # Try to extract Category + Action from the expected format
    category_match = re.search(
        r'Category:\s*(valid_agricultural|invalid_language|invalid_non_agricultural|'
        r'invalid_external_reference|invalid_compound_mixed|unsafe_illegal|'
        r'political_controversial|cultural_sensitive|role_obfuscation)',
        raw, re.IGNORECASE
    )
    action_match = re.search(r'Action:\s*(.+)', raw, re.IGNORECASE)

    if category_match:
        category = category_match.group(1).lower()
        action = action_match.group(1).strip() if action_match else ACTION_MAP.get(category, "Proceed with the query")
        return QueryModerationResult(category=category, action=action)

    # Fallback: scan raw output for any known category keyword
    raw_lower = raw.lower()
    for cat in VALID_CATEGORIES:
        if cat in raw_lower:
            return QueryModerationResult(category=cat, action=ACTION_MAP[cat])

    # If model says unsafe/violation/blocked → block it
    if any(word in raw_lower for word in ["unsafe", "violation", "blocked", "harmful", "illegal"]):
        return QueryModerationResult(
            category="unsafe_illegal",
            action=ACTION_MAP["unsafe_illegal"]
        )

    # Default: allow (be generous as per prompt instructions)
    return QueryModerationResult(
        category="valid_agricultural",
        action=ACTION_MAP["valid_agricultural"]
    )


async def run_moderation(user_message: str) -> QueryModerationResult:
    """Call the safeguard model directly without pydantic-ai Agent overhead."""
    system_prompt = get_prompt('moderation_system')

    response = await MODERATION_CLIENT.chat.completions.create(
        model=_MODERATION_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=128,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_moderation_response(raw)