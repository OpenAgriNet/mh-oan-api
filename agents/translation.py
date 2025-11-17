import os
from pydantic import BaseModel, Field
from typing import Literal
from pydantic_ai import Agent
from helpers.utils import get_prompt
from dotenv import load_dotenv
import logfire
from pydantic_ai.models import ModelSettings
from agents.models import LLM_MODEL

load_dotenv()

logfire.configure(scrubbing=False)

translation_agent = Agent(
    LLM_MODEL,
    system_prompt=get_prompt('translation.md'),
    instrument=True,
    retries=3
    # model_settings=ModelSettings(max_tokens=256)
)