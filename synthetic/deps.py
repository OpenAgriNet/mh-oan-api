from copy import deepcopy
from dataclasses import replace
from typing import List, Optional

from pydantic import BaseModel, Field
from langcodes import Language
from datetime import datetime
from pydantic_ai.messages import ModelResponse, ThinkingPart


class FarmerContext(BaseModel):
    """Context for the farmer agent in MH-OAN synthetic conversations.

    Extends the production FarmerContext with additional fields needed
    for mock tools to return data consistent with the simulated farmer.
    """
    query: str = Field(description="The user's question.")
    lang_code: str = Field(description="The language code of the user's question.", default='mr')
    session_id: str = Field(description="The session ID for the conversation.")
    moderation_str: Optional[str] = Field(default=None, description="The moderation result.")
    today_date: datetime = Field(description="Today's date.")
    farmer_id: Optional[str] = Field(default=None, description="The farmer ID (Agristack).")

    # Synthetic farmer profile fields for mock tools
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_state: Optional[str] = "Maharashtra"
    farmer_district: Optional[str] = None
    farmer_taluka: Optional[str] = None
    farmer_village: Optional[str] = None
    farmer_village_code: Optional[str] = None
    farmer_crops: Optional[list[str]] = None
    farmer_land_acres: Optional[float] = None
    farmer_gender: Optional[str] = None
    farmer_caste_category: Optional[str] = None
    farmer_latitude: Optional[float] = None
    farmer_longitude: Optional[float] = None
    farmer_is_pocra: Optional[bool] = None

    def update_moderation_str(self, moderation_str: str):
        self.moderation_str = moderation_str

    def _language_string(self):
        if self.lang_code:
            return f"**Selected Language:** {Language.get(self.lang_code).display_name()}"
        return None

    def _query_string(self):
        return "**User:** " + '"' + self.query + '"'

    def _moderation_string(self):
        if self.moderation_str:
            return self.moderation_str
        return None

    def _agristack_availability_string(self):
        if self.farmer_id:
            return "**Agristack Information Availability**: ✅"
        else:
            return "**Agristack Information Availability**: ❌"

    def get_user_message(self):
        strings = [self._query_string(), self._language_string(), self._moderation_string(), self._agristack_availability_string()]
        return "\n".join([x for x in strings if x])

    def get_today_date_str(self) -> str:
        return self.today_date.strftime('%A, %d %B %Y')


# ---------------------------------------------------------------------------
# Conversation history helpers for moderation context
# ---------------------------------------------------------------------------


def get_message_pairs(history: list, limit: int = None) -> List[List]:
    """Extract user/assistant message part pairs from history (newest first)."""
    if not history:
        return []

    pairs = []
    i = len(history) - 1

    while i > 0 and (limit is None or len(pairs) < limit):
        assistant_idx = None
        text_part = None
        for j in range(i, -1, -1):
            for part in history[j].parts:
                if getattr(part, "part_kind", "") == "text":
                    assistant_idx = j
                    text_part = part
                    break
            if assistant_idx is not None:
                break

        if assistant_idx is None or text_part is None:
            break

        user_idx = None
        user_part = None
        for j in range(assistant_idx - 1, -1, -1):
            for part in history[j].parts:
                if getattr(part, "part_kind", "") == "user-prompt":
                    user_idx = j
                    user_part = part
                    break
            if user_idx is not None:
                break

        if user_idx is None or user_part is None:
            break

        pairs.append([deepcopy(user_part), deepcopy(text_part)])
        i = user_idx - 1

    return pairs


def format_message_pairs(history: list, limit: int = None) -> List[str]:
    """Format user/assistant message pairs as strings."""
    pairs = get_message_pairs(history, limit)
    formatted = []
    for user_part, assistant_part in pairs:
        formatted.append(
            f"**User Message**:\n{user_part.content}\n\n"
            f"**Assistant Message**:\n{assistant_part.content}"
        )
    return formatted


def strip_thinking(history: list) -> list:
    """Remove ThinkingPart from ModelResponse messages."""
    cleaned = []
    for msg in history:
        if isinstance(msg, ModelResponse):
            filtered = [p for p in msg.parts if not isinstance(p, ThinkingPart)]
            cleaned.append(replace(msg, parts=filtered) if filtered != list(msg.parts) else msg)
        else:
            cleaned.append(msg)
    return cleaned


def build_moderation_input(user_text: str, agrinet_history: list, limit: int = 3) -> str:
    """Build the moderation prompt with conversation context."""
    message_pairs = "\n\n".join(format_message_pairs(agrinet_history, limit))
    if message_pairs:
        return f"**Conversation**\n\n{message_pairs}\n\n---\n\n{user_text}"
    return user_text
