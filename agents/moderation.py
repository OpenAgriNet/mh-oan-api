from pydantic import BaseModel, Field
from typing import Literal
from pydantic_ai import Agent, PromptedOutput
from helpers.utils import get_prompt
from pydantic_ai.models import ModelSettings
from agents.models import MODERATION_MODEL
from dotenv import load_dotenv

load_dotenv()

class QueryModerationResult(BaseModel):
    """Moderation result of the query."""
    category: Literal["valid_agricultural",
                      "invalid_language", # NOTE: Added this category that was missing here but was present in the prompt
                      "invalid_non_agricultural",
                      "invalid_external_reference",
                      "invalid_compound_mixed",
                      "unsafe_illegal",
                      "political_controversial",
                      "cultural_sensitive",
                      "role_obfuscation"] = Field(..., description="Moderation category of the user's message.")
    action: str = Field(..., description="Action to take on the query, always in English.")

    def __str__(self):
        category_str = self.category.replace("_", " ").title()
        if self.category == "valid_agricultural":
            tick = "✅"
        else:
            tick = "❌"
        return f"**Moderation Compliance:** {tick} {self.action} ({category_str})"

moderation_agent = Agent(
    model=MODERATION_MODEL,
    name="Moderation Agent",
    system_prompt=get_prompt('moderation_system'),
    instrument=True,
    output_type=PromptedOutput(QueryModerationResult),
    retries=2,
    # gpt-oss-safeguard-20b recommended settings
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=0.95,
        max_tokens=1024,
    )
)