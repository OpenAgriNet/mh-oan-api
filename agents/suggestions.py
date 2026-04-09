from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.settings import ModelSettings
from typing import List
from helpers.utils import get_prompt, get_today_date_str, get_crop_season
from agents.models import AGRINET_MODEL, VLLM_EXTRA_BODY
from agents.tools.search import search_documents
from agents.deps import FarmerContext
from dotenv import load_dotenv
load_dotenv()

suggestions_agent = Agent(
    name="Suggestions Agent",
    model=AGRINET_MODEL,
    instrument=True,
    output_type=List[str],
    deps_type=FarmerContext,
    retries=3,
    end_strategy="exhaustive",
    tools=[
        Tool(
            search_documents,
            takes_ctx=False,
        )
    ],
    model_settings=ModelSettings(
        parallel_tool_calls=False,
        extra_body=VLLM_EXTRA_BODY,
    )
)

@suggestions_agent.system_prompt(dynamic=True)
def get_suggestions_system_prompt(ctx: RunContext[FarmerContext]):
    lang_code = ctx.deps.lang_code or "en"
    prompt_name = f"suggestions_{lang_code}"
    return get_prompt(prompt_name, context={
        "today_date": get_today_date_str(),
        "crop_season": get_crop_season(),
    })