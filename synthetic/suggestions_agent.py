from pydantic_ai import Agent, RunContext, NativeOutput
from synthetic.utils import get_prompt
from synthetic.models import LLM_AGRINET_MODEL, ENABLE_INSTRUMENTATION
from typing import List
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from synthetic.deps import FarmerContext

SUGGESTIONS_MODEL_SETTINGS = OpenAIResponsesModelSettings(
    parallel_tool_calls=True,
    timeout=120,
    openai_text_verbosity="low",
    openai_reasoning_effort="medium",
)



suggestions_agent = Agent(
    model=LLM_AGRINET_MODEL,
    name="Suggestions Agent",
    instrument=ENABLE_INSTRUMENTATION,
    output_type=NativeOutput(List[str], name='suggestions', description='A list of suggested questions for the farmer to ask.'),
    deps_type=FarmerContext,
    retries=3,
    end_strategy='exhaustive',
    model_settings=SUGGESTIONS_MODEL_SETTINGS,
)


@suggestions_agent.system_prompt(dynamic=True)
def get_system_prompt(ctx: RunContext[FarmerContext]):
    deps = ctx.deps
    lang_code = deps.lang_code or "en"
    # Bhili: use English instructions; outputs are translated to Bhili in generate_suggestions.
    prompt_lang = "en" if lang_code == "bhb" else lang_code
    prompt_name = f"suggestions_{prompt_lang}"
    return get_prompt(prompt_name, context={
        'today_date': deps.get_today_date_str(),
        'crop_season': deps.crop_season,
    })
